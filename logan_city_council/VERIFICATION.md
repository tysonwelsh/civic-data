# Verification — Logan City Council data repo

**Date:** 2026-06-26
**Method:** data-integrity numbers independently RECOMPUTED from disk (csv-aware Python). Election
winners were externally cross-checked during the build (sources in `election_results/CLAUDE.md`);
re-confirmed here against those. (This repo was finalized by the orchestrator after the overnight
build agents completed their data; the independent recompute below is the QA pass.)

## Summary table

| Dataset | Status | Recomputed | Notes |
|---|---|---|---|
| Minutes | **PASS** | 198 index = 198 disk = 198 JSONs | 2020–2026; 0 header-only stubs; **0 iCloud dataless files** |
| Votes | **PASS** | 783 motions · 2,791 rows · 28 contested | per-member roll-calls; csv.writer-quoted |
| — body | **PASS** | Council 748 / RDA 35 motions (2,685 / 106 rows) | RDA recesses split into own files + tagged |
| — mayor roster | **PASS** | no leak | Daines (2021 mayor) 0 vote rows; Mark A. Anderson 0 rows in 2026 (mayor) but votes 2019–25 (councilmember); **Amy Z. Anderson and Mark A. Anderson kept distinct** (463 vs 445 votes) |
| Elections | **PASS** | 11 races · 55 candidates · 1,596 precinct rows | **independently re-confirmed 2026-06-26** — 6/6 general-election winners match external sources (Cache Valley Daily/UPR/hjnews/SLTrib); 2023 recount verified (Lt.-Gov-overseen, winners unchanged, Simmonds over Needham by ~16-19). See `election_results/ELECTION_VERIFICATION.md` |
| Comments | **PASS** | clean CSV = 0 rows; speaker log = 633 | in-minutes-only verdict; speaker log correctly labeled NOT comments |
| Geo | **PASS** | city polygon + 25 precincts | true EPSG:4326 (not UTM); City Hall → INSIDE, SLC/North Logan → OUTSIDE |

**Overall verdict: PASS.**

## Detail
- **Minutes ↔ index ↔ JSON** reconcile exactly (198 each). 0 dataless stubs (repo is in `~/civic-data`,
  outside iCloud). 149 Council + 49 RDA files (RDA = same-night recess segments split out).
- **Votes:** 783 motions / 2,791 member-vote rows / 28 contested. Per-member `Name: Aye/Nay` roll-calls
  parsed; page-footer/`DRAFT` lines filtered so they don't break vote blocks. Body keyed off slug
  (`city-council-meeting`→Council, `redevelopment-agency-meeting`→RDA).
- **Mayor non-voting confirmed:** the separately-elected mayor never appears as a routine voter
  (Daines 0 rows; Mark A. Anderson correctly votes as councilmember 2019–2025, 0 rows once mayor 2026).
- **Two-Anderson disambiguation works:** Amy Z. Anderson (council 2021) and Mark A. Anderson are
  distinct members in `all_votes.csv`, not collapsed.
- **Elections:** 11 races; winners cross-checked against local press at build time; Logan
  self-administered 2019/2021 (city PDFs), county certified canvass for 2023 (NOT the higher
  unofficial portal numbers), Enhanced Voting API for 2025. The 2023 Cache County integrity
  investigation/recount did not change winners. Precinct sums reconcile to certified totals for
  2019/2021/2023.
- **Recommended (optional):** a fresh fully-independent verification agent re-running the external
  election lookups would harden the Elections row further; the build-time confirmation + internal
  reconciliation are documented above.

**2026-07-02 (3.1) council-vote validation:** shared validator installed as `meeting_minutes/validate_votes.py` and run — 2,791 rows / 783 motions (509 named, 274 tally-only); 0 schema/date/vocab defects, 0 malformed motion groups, 0 double votes; tally-vs-counted 508/509 with the 1 mismatch a known partial dissent-only record (2020-08-18 m2, '4-1 Pass (no names)' with the lone dissenter named); 0 unexplained.

**2026-07-20 (TODO-b) addendum — +5 council motions recovered (grammar-gap fix):** the original attestation above stands; the extractor now also captures the clerk-dropped-"Motion by" form (`ACTION. <mover> seconded by <seconder> to …`, added as `ANCHOR3` in `extract_votes.py`), recovering 5 genuinely-missed 5-0 council motions — 2023-05-02 **Ordinance 23-15** (Tempki easement vacation, TODO-b target) + Res 23-13, and 2025-04-01 Res 25-11/25-12/25-13. New totals: **788 motions / 2,816 rows** (Council 753 / 2,710; RDA unchanged 35 / 106); 28 contested unchanged (all recoveries unanimous). Byte-stability proven: 0 pre-existing `(source,date,body,motion_no,member,vote)` rows changed (recoveries append after the meeting's existing motion_nos). validate_city.py 26 PASS / 0 WARN / 0 FAIL; db INTEGRITY OK.

**2026-07-20 (Ord 25-21 lead) addendum — +1 council motion recovered (word-scramble fix):** the
extractor now also captures a WORD-SCRAMBLED adoption form the clerk produced by transposing the
mover-name / "by" / seconder-name / "seconded by" tokens (`ANCHOR4` in `extract_votes.py`). Sole
corpus instance — 2025-12-02 `ACTION. Motion Councilmember A. Anderson by Vice Chair Johnson
seconded by to adopt Ordinance 25-21 … (4-0)` — recovered as **2025-12-02 m4, Ordinance, 4-0 Pass**
(A. Anderson / Johnson / López / Simmonds all Aye; `VACANT` seat excluded). **Mover/seconder left
BLANK** — the scramble makes the two names' mover/seconder order genuinely ambiguous (position →
A. Anderson; the surviving `…by Vice Chair Johnson` preposition → Johnson); per the never-fabricate
rule neither is guessed. New totals: **789 motions / 2,820 rows** (Council 754 / 2,714; RDA
unchanged 35 / 106); 28 contested unchanged (recovery unanimous). Byte-stability proven via
`comm -23` on sorted `all_votes.csv` pre/post — every changed line is dated 2025-12-02; the only
deltas are the 4 new Ord 25-21 rows plus the mechanical `motion_no` renumber of 25-22 (m4→m5) and
25-47 (m5→m6), content otherwise byte-identical. Extractor idempotent. validate_city.py 26 PASS /
0 WARN / 0 FAIL; db INTEGRITY OK.
