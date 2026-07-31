# VERIFICATION — Holladay City civic-data repo

Independent QA of the newly built Holladay repo. Method: reconcile every doubly-stored fact,
ground-truth sampled meetings against the source minutes text, confirm the structural quirks
(voting mayor, in-session RDA/LBA, prose results, Yes→Aye normalization), and cross-check the
election winners against outside sources. **No canonical CSV, minutes file, or extractor logic
was mutated during verification** (only stale doc text was corrected — see §7).

Verified 2026-07-12. `python3 scripts/validate_city.py holladay_city_council` = **20 PASS /
5 WARN / 0 FAIL** (the 5 WARNs are all expected and explained below).

## 0. Verdict per dataset

| Dataset | Result | Notes |
|---|---|---|
| Council minutes + votes (Council/RDA/LBA) | **PASS** | 152 files, 702 motions, 2,483 rows; reconciles exactly |
| Planning Commission minutes + votes | **PASS** | 45 files, 167 motions, 610 rows; reconciles exactly |
| Vote-value vocabulary | **PASS** | 0 `Yes`/`No` remain — all normalized to Aye/Nay per SCHEMA_SPEC §4 |
| Relational db (`db/civic.db`) | **PASS** | 869 motions / 2,702 votes; the CSV−db delta of +10 is fully explained (§4) |
| Elections | **PASS** | 34 races 2007–2025; 2021/2023/2025 winners cross-checked to outside sources (§6) |
| Public comments | **PASS (honest-empty)** | submit-only city; header-only `all_comments_clean.csv` by design |
| Geo | **PASS** | official 5-district polygon layer; City Hall → District 1 (§5) |
| Weeks / derived | **PASS** | weekly vote sum 2,483 == flat total; not stale |

## 1. Row / motion / body reconciliation (both bodies)

Per-meeting `votes/**/*.json` expand to exactly the flat CSV rows:

| Body | JSON files | Motions | Expanded rows | `all_votes.csv` rows | Match |
|---|---|---|---|---|---|
| meeting_minutes | 152 | 702 | 2,483 | 2,483 | ✅ |
| planning_commission | 45 | 167 | 610 | 610 | ✅ |

Motions by body (council CSV): **Council 678 · RDA 21 · LBA 3 = 702**; PC 167. This matches the
`body` column tallies (Council 2,411 + RDA 60 + LBA 12 = 2,483 rows).

**Index reconcile:** every `source` path in each `all_votes.csv` exists in that dataset's
`minutes_index.csv` (0 missing). Council index = 152 paths (145 carry ≥1 motion; 7 informational
docs carry none — expected). PC index = 45 paths (44 carry motions).

## 2. Structural quirks confirmed against source text

**Voting Mayor, max council roll = 6.** Roll-size distribution over named council motions:
`{1:4, 3:5, 4:27, 5:138, 6:226}` — **max = 6**, never 7. 226 motions carry a full 6-member roll.
**365 mayor vote-rows** (`is_mayor:true`), all attributed to the two people who have held the
mayor's chair: **Dahle** (2020–2025) and **Fotheringham** (2026). Both flagged
`mayor_rows_seen=yes` in `roster.csv`.

**Jan-2026 turnover** (roster is OBSERVED from the vote rows, corroborated by the geo layer's
`Representative` field and the 2026-02-05 attendance block):

| Seat | Through 2025 | From Jan-2026 |
|---|---|---|
| Mayor (citywide) | Robert **Dahle** | Paul **Fotheringham** |
| District 1 | Ty **Brewer** | David **Sundwall** |
| District 3 | Paul **Fotheringham** | Natalie **Bradley** |

Members-by-year confirms the swap cleanly: 2025 = {Brewer, Dahle, Durham, Fotheringham, Gray,
Quinn}; 2026 = {Bradley, Durham, Fotheringham, Gray, Quinn, Sundwall}. Durham (D2), Quinn (D4),
Gray (D5) continue.

## 3. Ground-truth spot-checks (source minutes quoted)

Eight meetings sampled across eras and bodies; every sampled roll matches the source **exactly**,
and the extractor records only the names the source printed (no Present-fill, no fabrication).

1. **Legacy 2020 prose roll — `2020-03-12` (file 607777), motion 1.** Source: *"The Council roll
   call vote was as follows: Council Members Petersen, Fotheringham, Quinn, Gibbons and Mayor
   Dahle in favor. Resolution 2020-13 was approved by a unanimous vote."* CSV: exactly those 5
   members, all `Aye`. (Durham, though a 2020 member, is correctly **absent** from this roll — the
   source did not name him. Honest, not a miss.)
2. **Modern Yes→Aye — `2025-07-17` (file 1306917), motions 1–3.** Source prints
   *"Vote on motion: Council Member Durham-Yes, Council Member Fotheringham-Yes, Council Member
   Quinn-Yes, Council Member Gray, Mayor Dahle-Yes."* CSV stores **Aye** for Durham, Fotheringham,
   Quinn, Dahle — and correctly **omits Gray**, whose name the source printed with **no vote
   token** ("Council Member Gray,"). Normalization + honest-omission both verified in one motion.
3. **LBA in-session — `2025-10-02` (file 1375585), motions 5 & 6.** Source line 180: *"Council
   Member Fotheringham moved to RECESS the City Council Meeting and RECONVENE in a Local Building
   Authority ("LBA") Board Meeting"*; the subsequent closed-session motions are tagged `body=LBA`
   by the section walk. Motion 5 names 6 (Durham, Brewer, Fotheringham, Quinn, Gray, Mayor Dahle —
   all Aye); motion 6 names 5 (Brewer correctly omitted — the prose roll lists only Durham,
   Fotheringham, Quinn, Gray, Mayor Dahle). Both match source.
4. **RDA in-session — `2021-08-26` (file 768663), motion 6.** Source line 263: *"Recess City
   Council into an RDA Meeting … Chair Gibbons called the RDA Meeting to order at approximately
   6:45 p.m."* The post-recess motion is tagged `body=RDA` (Fotheringham, Quinn, Dahle, Gibbons —
   all Aye). Faithful section-walk.
5–8. Four additional council motions across 2022–2025 (unanimous consent → blank member/vote;
   contested rolls) sampled inline while auditing — all consistent with the printed minutes.

## 4. Relational db reconciliation

`db/civic.db`: **body 4** (Council/RDA/LBA/PlanningCommission) · **person 26** · **meeting 194**
(Council 140 + RDA 9 + LBA 1 + PC 44) · **application 125** · **motion 869** (Council 678 · PC 167
· RDA 21 · LBA 3) · **vote 2,702** · **role 37** · **referral 4** (all medium, Council←PC).
Views present: `v_contested` (17 named-dissent motions), `v_member_record`, `v_project_timeline`,
`v_referral_chain`.

**CSV−db vote delta = +10, fully explained.** The two `all_votes.csv` carry 2,712 named member
rows; the db holds 2,702 votes. The difference is the **10 duplicate `(source,motion_no,member)`
rows** the `vote(motion_id,person_id)` UNIQUE collapses — all in the **PC**, all member **Layton**,
across six 2022 PC meetings (motions on files 870741, 934075, 934073, 934057, 934053). This is a
build-time recording artifact (a name printed twice in an early-2022 full-name PC roll), not a db
defect. Logged as a dedup follow-up in the repo-root `TODO.md`. See the audit report for the full
list.

## 5. Geo

`geo/council_districts.geojson` is Holladay's **own official** 5-district polygon layer ("as
amended 2022", ArcGIS Hub `d0cb510277ee4f0f989c9a5de4d0a6da`) — not precinct-derived. Point-in-
polygon of **City Hall (4580 S 2300 E)** → **District 1**, matching the layer's `Representative`
field (Sundwall). The Mayor is citywide and correctly not returned.

## 6. External election cross-check (browser UA)

`election_results/holladay_races.csv` = **34 races (2007–2025)**. The Cycle-A seats (Mayor + D1 +
D3) and Cycle-B seats (D2/D4/D5) alternate as documented. Winners for the three most recent cycles
cross-checked against outside sources:

| Race | Repo winner (certified SOVC) | Outside source | Agree |
|---|---|---|---|
| 2021 Mayor | Robert M. Dahle (unopposed) | SLTrib / Holladay Journal: Dahle unopposed, re-elected | ✅ |
| 2021 D1 | D. Ty Brewer (671 v. Hilton 608) | Holladay Journal / ABC4: Brewer def. Hilton | ✅ |
| 2021 D3 | Paul S. Fotheringham (unopposed) | Holladay Journal: Fotheringham unopposed | ✅ |
| 2023 D4 | Drew B. Quinn (1,073 v. Tracy 412) | internal-consistent (roster: Quinn continuous) | ✅¹ |
| 2025 Mayor | Paul S. Fotheringham (5,601 v. Watts 4,219) | SLTrib 2025-11-04: Fotheringham 56.8% v. Watts 43.2% | ✅ |
| 2025 D1 | David Hammon Sundwall (1,159 v. Bilstad 560) | Utah election-results site: Sundwall 1,159 / Bilstad 560 | ✅ |
| 2025 D3 | Natalie Bellamy Bradley (1,068 v. Jones 696) | Utah election-results site: Bradley 1,068 / Jones 696 | ✅ |

The **Dahle→Fotheringham** mayoral handoff is externally corroborated: Mayor Dahle did not seek
re-election in 2025 (SLTrib), and Fotheringham — the sitting D3 councilmember — won the open seat,
vacating D3 to Bradley while Brewer's D1 went to Sundwall. This is exactly the roster turnover the
vote data shows at the Jan-2026 seating.

¹ 2023 D4 not separately web-confirmed; Quinn's continuous roster presence (2020→2026) and the
certified SOVC row are internally consistent. Election-night unofficial vote counts reported by
news outlets differ in magnitude from the certified SOVC totals used here (e.g. 2021 Brewer 503
election-night vs 671 certified) — expected; winners and margins direction match.

## 7. Doc corrections applied (stale text only)

The extractor was fixed during the build to normalize the printed `Yes/No` council tokens to
`Aye/Nay` (SCHEMA_SPEC §4 controlled vocabulary), but three doc strings still described vote
values as "stored verbatim (Yes/No)". Corrected in place (no logic touched):
- `meeting_minutes/extract_votes.py` docstring
- `planning_commission/extract_votes.py` docstring
- `meeting_minutes/CLAUDE.md` (the `all_votes.csv` field note)

## 8. Known WARNs — all expected, none defects

- **`a.layout`** — missing optional README/CLAUDE/VERIFICATION at build time (this pass creates them).
- **`d.index` × 2** — `minutes_index.csv` carries a documented extra `body` column.
- **`f.tally[meeting_minutes]` 0/232** — Holladay `result` strings are **prose** ("…adopted by a
  unanimous vote"), never numeric tallies, so the numeric-tally cross-check matches 0 by design.
  The parsed outcome lives in `motions_std.csv` — **outcome coverage 864/869 motions carry a
  non-blank standardized `outcome`** (Pass 856 / Fail 7 / Continued 5 / Died 1), i.e. essentially
  full coverage; the tally WARN reflects the source's prose style, not lost data.
- **`h.db` +10** — the PC Layton duplicate rows (§4), collapsed by the db's UNIQUE; documented.

## 9. Blind spots (what this verification did NOT cover)

- 2023 D4 winner was checked for internal consistency only, not against a distinct web source.
- Ground-truthing sampled 8 of 197 meetings; the statistical corpus screen (both bodies, CLEAN,
  0 stubs / 0 low-alpha) backstops the unsampled remainder.
- PC 2020/2021/2023 minutes are an upstream PMN publishing gap — completeness there is bounded
  by what the city posts, not by the build. *(2026-07-16 update: 27 of the 89 gap rows —
  2020-01→09 + 2021-01→06 — were recovered from the former city WordPress site via the Wayback
  Machine and promoted into `planning_commission/` with `provenance=wayback_minutes`; 7 of the
  new motions were ground-truth spot-checked against source text verbatim. 62 gap rows remain in
  `minutes_unrecovered.csv`.)*
