# Verification — St. George (Utah) City Council Data Repo

> **Addendum (2026-07-02, audit-driven repair — wrong 2025-10-09 work-meeting minutes):**
> The repo-wide audit (`_audits/2026-07-02/report.md`, finding 5) confirmed that
> `meeting_minutes/minutes/2025/2025-10-06/2025-10-09_city-council-work-meeting.md` was the
> WRONG document — byte-identical in body to the 2025-10-16 regular-meeting minutes (its own
> header reads "REGULAR MEETING OCTOBER 16, 2025"). Root cause is a **city-side mis-upload**:
> re-fetched 2026-07-02, the published `2025.10.09  Work Meeting Minutes.pdf` is the same
> wrong PDF (md5 `96ec82b8…`) on BOTH the Revize portal and Utah PMN (file 1347731) — the
> real Oct 9 work-meeting minutes are not published anywhere found. The Oct 9 work meeting
> itself was real (PMN notice 4:00 PM; work agenda, agenda packet, and two recordings exist),
> so per the honest-gap rule the wrong file + its index row were **removed** and the meeting
> logged in `meeting_minutes/minutes_unrecovered.csv` (new file, schema shared with
> `planning_commission/minutes_unrecovered.csv`). Original in
> `_backups/2026-07-02/st_george_city_council/`.
> **The 110-vs-70 vote discrepancy explained:** of the 110 `all_votes.csv` rows dated
> 2025-10-09, only **70 were misdated duplicates** (extracted from the wrong work-meeting
> file = Oct 16's 14 motions / 70 rows); the other **40 rows are legitimate**, from the
> genuine `2025-10-09_city-council-regular-meeting.md` (a separate real meeting, 5:00 PM,
> Administrative Conference Room — its minutes verified 0.998-similar to PMN file 1347733).
> **Deltas after re-extraction:** `all_votes.csv` 8,382 → **8,312** rows (−70; remaining
> rows verified identical to before), motions 1,774 → 1,760 (−14), Council rows 8,317 →
> 8,247; contested 85 and the 2 documented tally quirks unchanged; 2025-10-09 now has
> exactly 40 rows and 2025-10-16 its own 70. `db/civic.db` rebuilt (2,765 motions ·
> 14,559 votes · 1,545 applications · INTEGRITY OK). NB: removing 7 applications shifted
> `application_id`s, so `db/referral_overrides.csv` (which keys on raw ids) was remapped
> old→new via each application's stable (source_file, motion_no) motion set — after the
> remap the referral layer reproduces the documented **117 links (15 high / 92 medium /
> 10 low)** exactly (verified identical link-for-link to the pre-repair db; without the
> remap the suppress overrides mis-target and 18 previously-suppressed links resurface).
> `weeks/` regenerated (248 bundles). Doc counts (306 meetings / 8,327–8,382 rows / 1,767–
> 1,774 motions) reconciled to 305 / 8,312 / 1,760.

**Verification date:** 2026-06-24
**Verifier:** Independent verification agent (did NOT build the data; adversarial QA).
**Repo:** `/Users/tysonwelsh/civic-data/st_george_city_council/` (moved from `~/Desktop/` after this verification)
**Counting method:** all dataset row counts via the Python `csv` module (NOT `wc -l`), per the verification standard (comment/motion text contains embedded newlines).
**External sources cross-checked:** KUER, Salt Lake Tribune (sltrib.com), St. George News (stgeorgeutah.com), KSL, plus the in-repo official Washington County certified `COUNTY TOTALS` rows.

---

## Summary table

| Dataset | Status | Rows | Coverage | Notes |
|---|---|---|---|---|
| **Minutes** | **PASS** | 306 files = 306 index rows | 2020–2026; 78/78 months covered | 215 Revize (2022–26) + 91 PMN (2020–21). File count == index count. 0 empty months. |
| **Votes** | **PASS** | 8,327 member-vote rows / 1,767 motions | 2020–2026 | 0 tally-vs-result mismatches across all 1,767 motions. 79 contested. 0 empty-member rows. All 269 source paths exist. |
| **Genuine comments** | **PASS** | 136 | 2023–2026 | 100% `source=written_published`. No `in_person_minutes` leakage. Per-year 2023:32 / 2024:39 / 2025:40 / 2026:25 = 136 (exact). All 53 source PDFs exist; spot-checks trace verbatim to raw PDFs. |
| **Speaker log** | **PASS** | 132 | 2022–2026 | Separate file, 100% `source=in_person_minutes`, clearly labeled "NOT public comments." Counts: 2022:24 / 2023:49 / 2024:19 / 2025:14 / 2026:26. |
| **Elections** | **PASS** | 11 races; 6,720 precinct rows; 63 candidate rows | 2019/2021/2023/2025 | Every winner externally corroborated (race-by-race below). 2019 totals match St. George News to the exact vote. |
| **Geo** | **PASS** | city_limits (1 polygon) + 79 precincts | at-large / in-city test | Tool runs offline; City Hall INSIDE (STG:41), Hurricane OUTSIDE. No fabricated districts. |
| **Weeks** | **PASS** | 248 bundles | 2020–2026 | `build_weeks.py` regenerates cleanly. Spot-check bundle 2025-05-01 votes.csv == canonical filtered (multiset match). |

**Overall: PASS.** No fabrication found. All counts in the brief reconcile.

---

## Per-dataset findings

### Minutes — PASS
- **306 `.md` files on disk == 306 rows in `minutes_index.csv`** (csv-module count). Matches the brief.
- By year: 2020:40, 2021:51, 2022:47, 2023:52, 2024:42, 2025:52, 2026:22.
- By source: **revize 215** (2022–26), **pmn 91** (2020–21). The 2020–21 PMN backfill is real and present.
- **Note (stale doc, not a defect):** `meeting_minutes/CLAUDE.md` still says "215 minutes (2022–2026)" and describes 2020–21 as an "acquisition gap." That doc predates the 2020–21 PMN backfill; the actual on-disk state (306, 2020–2026) supersedes it. Recommend updating that CLAUDE.md to avoid confusion.
- **Coverage:** every month from 2020-01 through 2026-06 has at least one City Council meeting (**78/78 months**, 0 gaps). Regular-meeting counts per year (32/28/40/42/31/39/11-partial) all meet or exceed the 1st/3rd-Thursday floor (~24/yr). 2026 partial through June as expected.
- 2020–21 minutes correctly normalize the inline `MOTION:`/`SECOND:`/`VOTE:` block (verified in source — see Votes).

### Votes — PASS
- **8,327 rows** (brief: ~8,327). **1,767 distinct motions.**
- **Tally consistency: 0 mismatches** — for every one of the 1,767 motions, the parsed Aye/Nay among recorded members equals the `result` string's `N-M`. This is a strong no-fabrication signal.
- **Contested (≥1 Nay): 79.**
- **Tally-only correctness:** 0 rows have an empty `member` (names-not-recorded motions correctly contribute zero member rows, per the standard — no invented voters).
- **All 269 distinct `source` paths exist on disk** (0 missing).
- **Provenance spot-check (8 rows incl. 2020–21), all traced to source and matched:**
  - 2020-12-17 m16 Hughes/Aye (4-0) → Twin Lakes/Gateway PD; source VOTE block lists Hughes/Smethurst/McArthur/Larkin all aye. ✔
  - 2020-06-04 m6 Smethurst/Aye, 2021-03-18 m1 Smethurst/Aye, 2021-10-21 m20 Curtis/Aye — all present in source. ✔
  - 2022-05-05, 2022-06-02, 2022-07-21, 2025-09-04 — all matched. ✔
  - **Mayor tie-break:** 2020-04-16 "Pike/Aye" on a **3-2** plat motion — source VOTE block: Hughes aye, Smethurst aye, McArthur nay, Larkin nay, **Mayor Pike – aye**, "The motion carried." Correctly captured. ✔
- **Roster is real and term-appropriate** (cross-checked vs `st_george_results_by_candidate.csv` + source PRESENT blocks):
  - 2020: Mayor Pike + Hughes, Smethurst, McArthur, Larkin, Randall.
  - 2021: Mayor Randall + Hughes, Smethurst, McArthur, Larkin, **Curtis** (Vardell Curtis confirmed in the 2021-03-18 PRESENT block).
  - 2022–23: Hughes, McArthur, Larkin, Larsen, Tanner (Mayor Randall).
  - 2024–25: McArthur → **Kemp** (transition confirmed).
  - 2026: Hughes → Mayor; **Anderson** appointed → Larkin, Larsen, Tanner, Kemp, Anderson.
  - All transitions (McArthur→Kemp 2024; Hughes→Mayor / Anderson 2026) present and externally corroborated.
- **Minor cosmetic finding (not a defect, not fabrication):** 2020–21 backfilled names appear as **bare surnames** (`Pike`, `Curtis`, `Smethurst`) instead of the "First Last" form used 2022+ (`Steve Kemp`, etc.). The `SURNAME_TO_FULL` normalization map did not extend to the 2020–21 PMN-era surnames. Every such name is a verified real official; this only affects join-by-name tidiness. Recommend extending the map (Pike→Jon Pike, Curtis→Vardell Curtis, Smethurst→Bryan Smethurst) for consistency.

### Genuine comments — PASS (KEY check for this repo)
- **136 rows in `all_comments_clean.csv`**, **100% `source=written_published`** — **zero `in_person_minutes` rows leaked in.**
- Per-year by `date_normalized`: **2023:32, 2024:39, 2025:40, 2026:25 = 136** — exact match to the brief and to `public_comments/CLAUDE.md`.
- The in-person speaker log (`minutes_speaker_log.csv`, 132 rows) is a **separate file**, 100% `source=in_person_minutes`, with an explicit header note that it is meeting-record notes, NOT public comments. Clean separation confirmed.
- **All 53 distinct `source_file` PDFs exist** (== 53 raw PDFs on disk). 0 missing.
- **Genuineness spot-check (5 random rows, all real member-of-public written submissions, none staff/petition):**
  - Tyson Smith 2024-01-30 (FrontRunner/2040 plan) — traced verbatim to the raw PDF: "Contact Name: Tyson Smith … extension of the Front Runner." ✔
  - Judy Carpenter-deBracy 2024-12-29 (SunRiver motel opposition), LeAnn Walters 2025-04-21 (dog-in-kennel complaint), Sianead Staheli 2026-03-14 (trash receptacle request), Paradise Afshar 2023-05-23 (CNN drag-show lawsuit inquiry) — all are residents'/individuals' own submissions. ✔
- Only **1** clean comment has a blank `contact_name` (flagged `no_name`); 135 have the empty flag. No anomalies.
- **Dropped audit (`all_comments_dropped.csv`, 11 rows) reconciles exactly:** `petition_signature_sheet`×4, `attachment_only`×4, `duplicate_forward`×3 — matches the documented routing-out of non-comment material (petition rosters, exhibit-only attachments, dup forwards). The "Mike McKee"/Citizen-Review-Board academic paper that slipped through was correctly moved to dropped.

### Speaker log — PASS
- 132 rows, separate, correctly labeled. Years 2022:24 / 2023:49 / 2024:19 / 2025:14 / 2026:26.
- 2020–2021 in-person comments are recorded **narratively** in those minutes (not the later "Link to comments by resident: <timestamp>" video-pointer format) and are intentionally NOT parsed into the speaker log — documented characteristic, **not failed**.

### Elections — PASS (see race-by-race external cross-check below)
- 11 races; **6,720** precinct rows; 63 candidate rows. At-large vote-for-N model applied (Council = multi-winner top-N).
- Roster implied by the elections (2019 Hughes/McArthur/Larkin won; 2021 Mayor Randall, Council Larsen/Tanner; 2023 Kemp/Hughes/Larkin; 2025 Mayor Hughes, Council Larsen/Tanner) **matches exactly who casts votes in `all_votes.csv`** after name normalization.

### Geo — PASS
- `city_limits.geojson` (1 St. George polygon) + `precincts.geojson` (79 overlapping precincts).
- `address_to_district.py` runs offline: `--latlon 37.1102 -113.5832` (City Hall) → **INSIDE** (precinct STG:41); `--latlon 37.1750 -113.2900` (near Hurricane) → **OUTSIDE**. Behaves as an in-city-limits check, returns `district=None` (correct — at-large, no districts). No fabricated district map.

### Weeks — PASS
- `python3 build_weeks.py` regenerates cleanly: 248 bundles (53 comment-weeks, 218 vote-weeks, 237 minutes-weeks). 248 week dirs on disk.
- Spot-check: `weeks/2025-05-01/votes.csv` has 65 rows, all dated 2025-05-01; the canonical `all_votes.csv` filtered to 2025-05-01 also yields 65 rows; **(member, vote, motion_no) multisets match exactly.**

---

## External election cross-check (race-by-race)

Required, outside-source verification. Repo winners below are from `st_george_races.csv`; "External" is a source *other than* the parsed county file.

| Cycle / Race | Repo winner(s) | External source & finding | Match |
|---|---|---|---|
| **2019 general Council (VF3)** | Hughes 7,717 (top); McArthur, Larkin won; Baca 6,331 first loser | St. George News: "Hughes 7,717 … McArthur 7,647 … Larkin 6,714 … Baca 6,331" — top 3 Hughes/McArthur/Larkin won. | ✔ exact (Hughes & Baca totals match to the vote) |
| **2021 general Mayor** | Michele Randall (over Hughes) | St. George News ("Michele Randall becomes first woman elected St. George Mayor"); KUER (Hughes "lost to Randall in 2021"). | ✔ |
| **2021 general Council (VF2)** | Larsen, Tanner | St. George News 2021 municipal results; corroborated by 2025 "re-election" framing. | ✔ |
| **2023 general Council (VF3)** | Kemp (top), Hughes, Larkin; Bennett first loser | KUER ("Kemp, Hughes and Larkin … win"); SLTrib; cedarcity/stgeorge News (Kemp replaced McArthur, beat Bennett & Smith). | ✔ |
| **2025 general Mayor** | Jimmie Hughes (over incumbent Randall) | KUER, SLTrib ("Hughes defeats incumbent Randall"), KSL, 890KDXU. | ✔ |
| **2025 general Council (VF2)** | Larsen, Tanner (re-elected) | St. George News / City of St. George ("Congratulations to Natalie Larsen and Michelle Tanner on their re-election"). | ✔ |
| 2026 council appointment (not a race) | Anderson seated | SLTrib & St. George News: Council appointed **Austin Anderson** (3-1) Jan 22 2026 to fill Hughes's vacated seat (Larkin voted for Leavitt). Matches `all_votes.csv` 2026 roster. | ✔ |

**Races checked: 7 (6 contested races + the 2026 appointment). Mismatches: 0.** Primary races (4 more) were not independently re-derived against news but their advancers are consistent with the general-race rosters that ARE corroborated; counted as covered by the general-race verification.

**Vote-total note (documented, not a defect):** secondary news outlets report **election-night** mayoral totals (2025 Hughes 10,287 / Randall 8,467; 2021 Randall partial) that differ from the repo's **certified county `COUNTY TOTALS`** (2025 Hughes 12,334 / Randall 9,859; 2021 Randall 11,614 / Hughes 9,434). This is the normal election-night-vs-certified-canvass gap; the repo correctly uses certified totals and documents the discrepancy in `election_results/CLAUDE.md`. **Winner identities and seat counts agree across all sources.**

---

## Gaps & recommendations

1. **Stale `meeting_minutes/CLAUDE.md`** — still states 215 minutes / 2022–26 only and calls 2020–21 an "acquisition gap." The repo now has 306 files (2020–2026) with the PMN backfill present and verified. Update the doc (cosmetic; on-disk data is correct). *Not a data defect.*
2. **2020–21 vote member names are bare surnames** (`Pike`/`Curtis`/`Smethurst`) vs "First Last" elsewhere. Extend `SURNAME_TO_FULL` for consistency in person-level joins. *Not fabrication — all are verified real officials.*
3. **No pre-2023 written public comments** — legitimate (the city's `public_comments.php` intake began 2023; `AVAILABILITY.md` documents this). 2022 covered by speaker log only. Not a gap to fix.
4. **In-person comment text is not transcribed** (minutes record only speaker/topic/timestamp). Video transcription is out of scope and correctly flagged as deferred.
5. **2026 is partial** (through ~June) for minutes and comments — expected, not a gap.
6. **Primary-race external re-derivation** is indirect (covered via the corroborated general rosters). If a fully independent primary cross-check is desired, pull the Enhanced Voting / county primary summaries — low priority since general winners all reconcile.

No fabricated members, dates, motions, votes, comments, or districts were found. Every derived row sampled traces to a real source document.

---

```json
{"overall":"PASS","by_dataset":{"minutes":"PASS","votes":"PASS","genuine_comments":"PASS","speaker_log":"PASS","elections":"PASS","geo":"PASS","weeks":"PASS"},"fabrication_found":false,"election_crosscheck":{"races_checked":7,"mismatches":[]},"key_findings":["306 minutes files == 306 index rows; 215 Revize + 91 PMN; 78/78 months 2020-01..2026-06 covered, 0 gaps","all_votes.csv 8327 rows / 1767 motions: 0 tally-vs-result mismatches, 0 empty-member rows, all 269 source paths exist, 79 contested","2020-04-16 Pike 3-2 mayoral tie-break verified verbatim against source minutes","all_comments_clean.csv = 136 rows, 100% written_published, ZERO in_person_minutes leakage; per-year 32/39/40/25 exact; 5 genuineness spot-checks trace verbatim to raw PDFs","speaker log 132 rows kept separate and labeled (100% in_person_minutes)","every election winner externally corroborated (KUER/SLTrib/St.George News); 2019 totals match to the exact vote; Anderson Jan-2026 appointment confirmed","weeks regenerate clean (248 bundles); 2025-05-01 bundle multiset-matches canonical"],"gaps":["meeting_minutes/CLAUDE.md is stale (says 215/2022-26; actual 306/2020-26) - doc-only","2020-21 vote names are bare surnames vs First-Last elsewhere - cosmetic normalization, not fabrication","no pre-2023 written comments (legitimate; AVAILABILITY.md documents); 2022 = speaker log only","2026 partial through ~June (expected)"]}
```

## 2026-07-02 addendum — duplicate member-vote adjudication (plan item 3.1 prep)

The repo validator flagged 3 duplicate `(source, motion_no, date, member)` pairs in
`planning_commission/all_votes.csv`. Source check: all three are **faithful source
contradictions** (kept verbatim in the CSV; resolved in the db):

- **2021-04-13 m6 (motion to table): Steve Kemp Aye+Nay.** The minutes print "AYES (5)"
  but list SIX names (Kemp among them, wrapped across a page break) and then "NAYS (2):
  Kemp, West". The NAYS list is the deliberate record; dropping Kemp from the ayes
  matches the printed (5) count. db resolves to **Nay**.
- **2025-02-25 m3 & m4: Austin Anderson Absent+Aye.** The roll opens "Chair Anderson –
  absent" (as in every vote that meeting) and later repeats "Chair Anderson – aye" in
  the slot that m1/m2 print as "Commissioner Chapman – aye" (Vice Chair Chapman, who was
  calling the votes, is otherwise missing from these rolls). Clerk slip; db resolves to
  **Absent** (no Aye is reassigned to Chapman — never fabricate).

Resolutions live in the new `db/vote_overrides.csv`, applied fail-loud by
`db/build_db.py` (park_city pattern; see db/SCHEMA.md). db rebuilt: 2,765 motions ·
14,559 votes (= 14,562 named rows − 3 merges) · 117 referrals unchanged. Validator
h.db: PASS ("+ 3 documented overrides").

**Known extraction gap — FIXED 2026-07-02 (plan item 3.5):** in the same 2025-02-25
file, motions 1–2 recorded only 2 of the 5 printed ayes. Root cause: the roll line
"Planning Commission Commissioner Chapman – aye" uses a title prefix outside the
extractor's fixed `ROLE_PREFIX` alternation, so `VOTE_LINE_RE` failed and the vote-block
parser hard-stopped there, also dropping the "Member Rogers – aye" / "Member Draper –
aye" lines below it. Fixed class-wide in `planning_commission/extract_votes.py`:
`VOTE_LINE_RE` now accepts a *run* of role tokens (same token class as the AYES-path
`ROLE_STRIP_RE`) instead of one fixed alternation. Regenerated (`--force`): all_votes
6,250 → 6,256 rows — the ONLY changes are +3 Aye rows each on 2025-02-25 m1/m2
(Lori Chapman, Ben Rogers, Teri Draper) and those motions' result strings
"Positive recommendation 2:0" → "5:0"; roster.csv identical; no other meeting changed.
Corpus-wide regex sweep: the two Chapman lines are the only lines the new pattern
newly matches; 23 lines it no longer matches are all 2020 narrative dialogue
("Chair Pro Tem Brager – <speech>"), which never carried vote values and contributed
no rows before or after. db rebuilt (14,568 named CSV rows = 14,565 votes + 3
documented `db/vote_overrides.csv` merges — the m3/m4 Anderson resolution is
undisturbed); referrals reproduce 117 links exactly; weeks rebuilt (248);
motions_std regenerated (only the two m1/m2 tallies changed, tally cross-check now
2,765/2,765); both validate_votes.py clean; validate_city.py 23 PASS / 0 FAIL.
Originals in `_backups/2026-07-02/st_george_city_council/planning_commission/`.

**Separate gaps surfaced by the same sweep (logged, NOT fixed here — different root
causes):** (1) `2024-12-10` and parts of `2024-04-09` PC minutes carry a line-number
gutter on every line ("25   MOTION:"), so no structural regex matches and those
meetings extract ZERO motions (2024-12-10 includes a real contested 3–2 failed
ridgeline motion); (2) joint PC/Council meeting files (e.g. 2022-08-25, 2024-02-29,
2026-05-28) print "Councilmember X – aye" roll calls that the PC extractor by design
does not capture (council votes in PC-indexed files). Both need their own scoped fix
with body attribution decided deliberately.

**2026-07-02 (3.1 cleanup):** removed `meeting_minutes/CLAUDE 2.md` — a stale duplicate
of `CLAUDE.md` from before the 2025-10-09 repair and the `body`-column retrofit (it still
claimed 306 files / 8,327 rows and lacked the body-tagging documentation). Verified
strictly superseded by diff; original backed up to
`_backups/2026-07-02/st_george_city_council/meeting_minutes/`.

**2026-07-02 (3.1) council-vote validation:** shared validator installed as `meeting_minutes/validate_votes.py` and run — 8,312 rows / 1,760 motions (all named); 0 schema/date/vocab defects, 0 malformed groups, 0 double votes; tally-vs-counted 1,760/1,760; the 2 unanimity-vs-roll quirks (2021-06-03 m7, 2021-11-18 m15) carry no numeric tally so they are covered by the extractor's own validation, noted in the report; 0 unexplained mismatches.
