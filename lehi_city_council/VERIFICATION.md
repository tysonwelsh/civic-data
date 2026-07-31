# Verification — Lehi, Utah city council data repo

> **Addendum (2026-07-02, audit-driven repair — duplicate Granicus events):** A repo-wide
> duplicate-body screen (`.claude/skills/audit-city-data/scripts/screen_corpus.py`) found **8
> same-date file pairs with identical bodies** that the original audit missed — 6 council + 2 PC —
> each a case of ONE minutes document attached to TWO consecutive Granicus events (Pre/Regular
> session, Oath-of-Office/Regular, PC work/regular), so the same meeting was parsed twice and its
> votes double-counted. **Verified at source:** all 16 `source_url` doc_ids were re-fetched
> (2026-07-02); each pair's two docs are **md5-identical to each other and distinct from every
> other pair's** (e.g. clip350/351 → `db59efc3…`, clip651/652 → `d5bf20fc…`, PC clip278/279 →
> `96343a7b…`). The known 2024-06-18 clip673/clip698 pair was re-verified as two REAL distinct
> meetings (different bodies: "City Council–Amended" vs "Joint City Council in Highland City";
> 10 vs 0 vote rows) and was NOT touched.
>
> **Removed** (one file per pair; kept the event matching the document's self-description —
> "Regular"/"City Council" over "Pre"/"Oath"; for byte-identical titles the lower clip_id):
> council 2021-02-09 clip351, 2024-04-23 clip651, 2024-05-28 clip667, 2024-09-10 clip696,
> 2026-01-06 clip934, 2026-01-27 clip946; PC 2020-02-06 clip279, 2024-04-25 clip654 — plus their
> 8 `minutes_index.csv` rows. Originals in `_backups/2026-07-02/lehi_city_council/`. (The kept
> 2026-01-06 clip936 doc self-states "January 6, 2025" — a **source clerk typo**, preserved
> verbatim: content is unambiguously the 2026 organizational meeting — Mayor Binns, the 2025+
> cohort, the 2026 meeting-schedule discussion; it is NOT the distinct 2025-01-07 work session.)
>
> **Deltas (all re-measured):** council minutes 181→175 (166 Council + 9 MBA), votes
> 1,306→1,253 motions / 6,412→6,147 rows (−265; contested 99 unchanged); PC minutes 162→160,
> votes 1,099→1,089 motions / 6,269→6,219 rows (−54; contested 142→140). Surviving rows verified
> **byte-identical as multisets** pre/post in both CSVs. `validate_votes.py` PASS both datasets
> (same 2 council source-typo tally mismatches; PC 8 tally + 2 outcome + 1 out-of-window
> unchanged). db rebuilt: meetings 289→281, applications 1,423→1,407, motions 2,405→2,342, votes
> 12,681→12,362, INTEGRITY OK. **Referrals 474→459** (db actual pre-repair was 474; docs' "471"
> was pre-existing drift): after normalizing removed→kept twin files, 458 of the pre-repair
> unique app-pairs reproduce; net change = **1 lost + 2 gained**, all mechanically traced to the
> dedup itself — duplicate applications sat in the linker's IDF corpus as extra documents,
> deflating their project tokens' weights. Post-dedup scores rose (e.g. 2026-01-27 m5 subject
> score 0.408→0.743, adding PC 2025-02-27 m6; Council 2025-12-16 m7 → PC 2025-12-04 m13 entered
> at 0.848), and one borderline high link (Council 2021-10-26 m3 → PC "North Subdivision") sat at
> exactly the 0.20 address+subject threshold pre-repair and fell just below it (sibling links'
> scores dropped ~0.001, e.g. 0.298→0.297, 0.100→0.099) — that project remains linked
> via its sibling motion 2021-10-26 m4 (0.297, high). `db/overrides.csv` and
> `db/referral_overrides.csv` are both empty — **no id remap needed**. weeks/ rebuilt (165
> bundles, count unchanged — every deduped date kept one file).
>
> **Knock-on fixes in additive datasets:** `ordinances/index.csv` — 18 rows' `source_url`/
> `minutes_source` remapped from removed files to their kept twins (clip651→652, 696→697,
> 946→947; identical motion numbering verified; diff is remap-only). The docs' "334 motions cite
> an ordinance number" claim was re-checked: a plain per-motion `Ordinance #N-YYYY` count on the
> **deduped** corpus = exactly 334, so the figure stands. `public_comments/minutes_speaker_log.csv`
> — 12 duplicate paraphrase rows removed (clip651×2, clip667×1, clip696×1, clip946×8), 160→148
> rows (README/CLAUDE previously said 161 — pre-existing off-by-one vs the file's actual 160);
> removal-only diff verified. `pmn_backfill/coverage.md` repo-count columns updated (per-date
> set-difference conclusions unaffected).
>
> **Final screen:** `screen_corpus.py` on both corpora → duplicate_bodies **0** except the
> verified-distinct 2024-06-18 pair (none — its bodies differ, so it never flags). The summary
> table below is the original 2026-06-26 verification record, retained as history.

**Date:** 2026-06-26
**Verifier:** independent verification agent (did not build the data). Every headline number
below was **recomputed from disk** with csv/json-aware Python (never `wc -l`). External
election winners were cross-checked against Lehi Free Press, Daily Herald, KSL, Deseret News,
and the Utah County / state canvass portals.

## Summary table

| Dataset | Status | Recomputed headline | Coverage | Notes |
|---|---|---|---|---|
| Minutes | **PASS** | 181 md files == 181 index rows == 181 vote JSONs | 2020–2026 (≥2020 floor met) | 0 header-only stubs (<200 B); **0 iCloud dataless** files |
| Votes | **PASS** | 1306 motions, 6412 member-vote rows | Council 1298 / RDA 0 / MBA 8; 99 contested; 4 Mayor tie-breaks | No Mayor leak; 0 internal tally mismatches; 6 spot-checks verbatim |
| Elections | **PASS** | 9 races, 58 candidate rows, 1688 precinct rows | 2019/2021/2023/2025, at-large | **Every winner externally confirmed**; Astill withdrawal handled correctly |
| Comments | **PASS** | 42 genuine comments; 160 speaker-log; 9 dropped | 2020 only (4 meetings) | Speaker-log correctly segregated + flagged |
| Geo | **PASS** | 1 city polygon, 55 precincts | city-limits (at-large) | True EPSG:4326 (lon/lat, not UTM); inside/outside correct |

**Overall verdict: PASS.**

---

## 1. Minutes — PASS

- `find minutes -name '*.md'` = **181**; `minutes_index.csv` = **181** rows; vote JSONs = **181**.
- Set-diff index↔disk (by basename, both directions) = **empty** — every indexed file exists
  and every file is indexed.
- Year coverage: 2020:25, 2021:27, 2022:31, 2023:30, 2024:36, 2025:27, 2026:5. Floor (≥2020) met.
- Stub audit: **0** files under 200 bytes — no header-only/empty-download stubs.
- **iCloud dataless audit:** `find . -name '*.md' -exec ls -lO {} \; | grep -ic dataless`
  = **0** across the entire repo (md/csv/json/geojson). Clean.

## 2. Votes — PASS

Recomputed from `all_votes.csv` + `votes/*.json`:
- **Motions: 1306** (claim 1306 ✓). **Member-vote rows: 6412** (claim 6412 ✓).
- **Body split (motions): Council 1298 / RDA 0 / MBA 8** (claim ✓). RDA=0 is by-design
  (Lehi minutes RDA business in a separate record; in-council recess brackets are empty).
- **Contested (≥1 nay): 99** (claim 99 ✓).
- All **148 unique `source` paths exist on disk** (0 missing).
- **Internal tally-vs-result consistency: 0 mismatches** — every `N:N` result string matches
  its recorded aye/nay names. (The 2 "source-typo" mismatches the build flagged are
  minutes-printed-summary vs named-roll-call, not CSV errors.)
- **names_recorded:false motions = 0** — every captured motion carries a named roll call, so
  no motion guesses members. (No tally-only stubs exist; the requested "tally-only" spot-check
  category is therefore empty by construction, which is the safe direction.)

### Critical Mayor-leak check — PASS (no leak)
Only **"Mark Johnson"** ever appears as a member, on exactly **4 rows** — the tie-breaks at
**2022-06-14, 2023-04-11, 2024-03-26, 2025-12-16** (matches the 4 claimed dates). **Paul Binns
never appears as a voter.** Per-year roster confirms the Mayor is tie-break-only, never routine.

### Roster plausibility — PASS
Member set: Albrecht, Hancock, Condie, Koivisto, Southwick, Newall, Stallings, Lockhart,
Harrison, Freeman (+ Johnson tie-break). Every voter maps to a real election winner (or the
appointed Lockhart / Mayor Johnson); no stray or fabricated names. 2026 cohort (Freeman,
Harrison, Lockhart, Newall, Stallings — 28 votes each) matches recon's current council.

### Six motion spot-checks against minutes text — all verbatim-confirmed
1. **Contested council** 2020-01-14 m8 — minutes: "Albrecht, No; Condie, No; Southwick, No;
   Hancock, No; and Koivisto, Yes. The motion failed." → CSV `1:4 Fail` ✓ (also proves
   line-wrapped + semicolon/"and"-separated capture).
2. **Mayor tie-break** 2024-03-26 m6 — minutes: "…Newall, No; and Stallings, No; Mayor
   Johnson, No. The motion FAILED with 2 in favor, 3 opposed. Mayor Johnson was the tie
   breaking vote." → CSV `2:3 Fail` with Johnson Nay folded in ✓.
3. **MBA** 2022-10-11 m1 — minutes: "Mr. Hancock, Yes; Mr. Southwick, Yes; Mr. Condie, Yes;
   Ms. Koivisto, Yes; Ms. Albrecht, Yes. The motion passed unanimously." → CSV `5:0 Pass`,
   body=MBA ✓ (also satisfies the "passed unanimously" tally check).
4. **Format-B label block (2025+)** 2025-12-22 m1 — "YES: Chris Condie, Paul Hancock, Heather
   Newall, Michelle Stallings. The motion passed unanimously." → CSV `4:0 Pass` (Albrecht
   absent due to the late-2025 vacancy) ✓ (proves comma-separated label-block capture).
5–6. Additional unanimous council/MBA roll calls in the same files reconciled.

## 3. Elections — PASS

- `lehi_races.csv` = **9 races**; `lehi_results_by_candidate.csv` = **58 rows**;
  `lehi_results_by_precinct.csv` = **1688 rows** (claim ✓).
- Multi-seat winner representation is **consistent** between the two files: every top-N
  candidate is `is_winner=True` (2019 & 2023-general: 3 each; 2021 & 2025-general: 2 each;
  2023 primary: 6; 2025 primary: 4/2).
- **2023 Astill withdrawal handled correctly:** in the 2023 primary, Corey Astill is rank 4
  (371 first-choice) with **`is_winner=False`**, and **K. Casey Glade is flagged advanced
  (is_winner=True)** in his place — exactly matching the LG-directed recount.

### External winner cross-check (every winner attempted)

| Race | File winner(s) | Outside source | Match |
|---|---|---|---|
| 2019 Council (3) | Albrecht, Southwick, Koivisto | Lehi Free Press "Revill out after Koivisto's late surge win… Albrecht and Southwick reelected" | ✅ |
| 2021 Mayor | Mark I. Johnson (over Riddle) | Lehi Free Press "Voters reelect Johnson, Condie and Hancock" | ✅ |
| 2021 Council RCV (2) | Condie (R8), Hancock (R7) | Lehi Free Press (same); Daily Herald | ✅ |
| 2023 Council general RCV (3) | Albrecht 2973, Stallings 2917, Newall 2863 | Lehi Free Press "Albrecht wins re-election, Stallings and Newall elected" | ✅ (incl. final-round totals) |
| 2023 Council **primary** (Astill) | Astill withdrew → Glade advanced (6 advance) | Daily Herald "Casey Glade continues to general after recount"; KSL/Deseret | ✅ |
| 2025 Mayor general | Paul Binns 53.5% over Albrecht 46.5% | Lehi Free Press "Binns elected Lehi Mayor" | ✅ |
| 2025 Council general (2) | Harrison, Freeman (Lockhart first loser) | Lehi Free Press "Binns, Harrison and Freeman prevail" | ✅ |
| 2025 Mayor primary (2 adv) | Albrecht, Binns | Lehi Free Press "Albrecht, Binns advance in Lehi Mayor Race" | ✅ |
| 2025 Council primary (4 adv) | Lockhart, Freeman, Harrison, Peterson (Hancock elim.) | Lehi Free Press "Longtime council members eliminated" | ✅ |

**Source URLs:**
- https://lehifreepress.com/2019/11/06/revill-out-after-koivistos-late-surge-win-to-city-council-seat-albrecht-and-southwick-reelected/
- https://lehifreepress.com/2021/11/02/voters-reelect-johnson-condie-and-hancock-parc-tax-passes/
- https://lehifreepress.com/2023/11/21/city-council-election-2023-albrecht-wins-re-election-stallings-and-newall-elected-to-first-terms/
- https://www.heraldextra.com/news/local/2023/sep/18/casey-glade-continues-to-general-election-for-lehi-city-council-after-recount/
- https://www.ksl.com/article/50734164/why-lehi-recounted-its-primary-election-results
- https://lehifreepress.com/2025/11/04/breaking-news-binns-elected-lehi-mayor/
- https://lehifreepress.com/2025/11/10/election-wrapup-binns-harrison-and-freeman-prevail-precinct-maps-winners-shared/
- https://lehifreepress.com/2025/08/12/albrecht-binns-advance-in-lehi-mayor-race-longtime-council-members-eliminated/

**Minor (documented, not errors):** the 2021/2023 RCV `final_votes` come from a different
canvass snapshot than `round1_votes` (the build flags the rcvis-doubling and EV-vs-rcvis
gaps); the **winner SET is identical** under either, which is the load-bearing fact. The
2025 council seat-deciding margin computes to **191** (Freeman 7163 − Lockhart 6972); a
news Friday-count cited 182 — final-certified vs intermediate; no concern.

### Roster cross-walk — PASS
Every council winner across cycles (2019 Albrecht/Southwick/Koivisto; 2021 Condie/Hancock;
2023 Stallings/Albrecht/Newall; 2025 Harrison/Freeman + appointed Lockhart) appears as a
voter in `all_votes.csv`, and every voter traces back to a winner or the Mayor. Only naming
nuance: "Mike Southwick" (votes) = "Mike V Southwick" (elections) — same person.

## 4. Comments — PASS

- `all_comments_clean.csv` = **42** rows, **all dated 2020** across the 4 expected meetings
  (2020-03-30, 04-13, 06-08, 06-22). 32 named + 10 anonymous = 42. Every row flagged
  `verbatim_written_comment_published_in_minutes`, source `online_written_comment_published_in_minutes`
  — genuine resident-submitted text, not paraphrase.
- `minutes_speaker_log.csv` = **160** data rows (after the leading note line), **all** flagged
  `clerk_paraphrase_not_written_comment`, with a header note declaring they are NOT comments.
  **Correctly kept OUT** of the comments CSV.
- `all_comments_dropped.csv` = 9 (segmentation artifacts). `AVAILABILITY.md` present and
  documents the full hunt; verdict **in-minutes-only** (genuine) / **eComment submit-only**
  (SpeakUp portal not publicly archived) — consistent with the data shape.
- Minor: speaker-log `date_normalized` column is empty (dates live only in the source text);
  cosmetic, no impact on the comments verdict.

## 5. Geo — PASS

- `city_boundary.geojson` = 1 feature; `precincts.geojson` = 55 features.
- **CRS is true EPSG:4326** — sample coords `(-111.83, 40.42)` are Utah lon/lat, **not UTM
  meters** (the slco/WVC mislabel trap is avoided); declared CRS = EPSG:4326.
- `address_to_district.py` runs offline:
  - `--latlon 40.3916 -111.8508` (City Hall area) → **INSIDE** Lehi city limits (25LE33).
  - `--latlon 40.2338 -111.6585` (Provo) → **OUTSIDE**, no Lehi representation.
- At-large model honored: no fabricated district map; precincts informational only.

## Gaps & recommendations (all minor / cosmetic)
1. `votes/_validation_report.txt` per-year roster under-prints 2026 (shows only Freeman) —
   the underlying CSV correctly has all 5 members at 28 votes each. Cosmetic report bug.
2. `minutes_speaker_log.csv` `date_normalized` is blank — populate from source if dates are
   needed for joins.
3. Elections `final_votes` canvass-snapshot caveats (2021 doubling, 2023 EV-vs-rcvis) are
   honestly disclosed; winner sets are unaffected. No action required.

**No fabrication, no Mayor vote-leak, no dataless stubs, no winner mismatch found.**

**2026-07-02 (3.1) council-vote validation:** bespoke `meeting_minutes/validate_votes.py` re-run — 1,253 motions, 2 tally-vs-printed-summary mismatches (both documented source typos, names authoritative), 0 outcome issues, 123 reviewed roster-size deviations, 4 mayor tie-breaks; shared-template checks (schema/dates, motion-group convention, double votes, tally-vs-counted): 0 hard failures, 0 unexplained mismatches.
