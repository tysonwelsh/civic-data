# Kearns — data verification

Independent QA of the `kearns_city_council/` repo. Companion to the graded audit at
`_audits/audit_2026-07-12.md` (read it for the full method and the ranked fix list).
`scripts/validate_city.py kearns_city_council` = **23 PASS / 2 WARN / 0 FAIL** (the
two WARNs are the missing top-level docs — created in this pass — and the benign
narrative-tally `f.tally`; see below).

## PASS/FAIL by dataset

| Dataset | Status | Notes |
|---|---|---|
| Council minutes — faithfulness | **PASS** | OCR + born-digital ground-truthed against raw PDFs; faithful |
| Council minutes — completeness | **PASS (backfilled 2026-07-12)** | township back-catalog harvested — 85 of 111 Meeting-Minutes-bearing 2017-2023 notices added (2018-07 → 2023); the 26 remaining are PMN-purged pre-mid-2018 file blobs + genuine no-minutes meetings; see §Coverage |
| Planning Commission minutes | **PASS** | clean MSD born-digital; OAM keys intact; 2017-2018 gap genuine |
| Vote extraction (Council + PC) | **PASS** | tally-style handled; contested abstain verified; db 5=5 |
| Elections (`kearns_races.csv`) | **PASS** | Valdez 2025 externally cross-checked exact; raw-SOVC provenance |
| Public comments | **PASS** (honest zero) | submit-only; header-only file correct by design |
| Geo (districts) | **PASS w/ caveat** | D2/D4 authoritative; D1/D3 honest unsplit residual |
| Derived (`db/`, `weeks/`) | **PASS** | exact reconciliation, 0 orphans, not stale |

## Reconciliation — flat CSV ↔ index ↔ JSON ↔ db (both bodies)

**Council (after the 2026-07-12 township backfill):** 117 minutes `.md` = 117 vote
JSON = 117 `minutes_index.csv` rows (117 minutes raws + 1 `supdocs` packet, correctly
excluded). `all_votes.csv` = **492 motions** (516 CSV rows: 484 tally-only placeholders
+ 32 named member+vote rows — 22 Aye / 8 Nay / 2 Abstain, from the township roll-call
motions the source names in full). **PC:** 43 `.md` = 43 JSON = 43 index rows = 43 raw
PDFs; `all_votes.csv` = **197 motions** (unchanged). `validate_votes.py` = PASS
(max-seat-5 respected, 0 off-roster names, CSV = JSON); `screen_corpus.py` = CLEAN
(0 stubs / 0 low-alpha).

**db/ + weeks/:** the on-disk derived layers still reflect the pre-backfill council
totals and are **pending regeneration** by the orchestrator (`build_weeks.py`,
`db/build_db.py`, `db/build_referrals.py`, then cities.db refederation). After that
rebuild `motion` = 492 + 197 = 689 council+PC, `vote` = 36 named rows (32 council +
4 PC abstains), and the weekly
sums will follow the new flat totals. The `2025-08-26` (and other adjourn-only /
canvass / cancellation) meetings hold 0 motions so create no meeting row — benign,
explained.

## Spot-checks (source quoted)

1. **Council OCR, 2024-01-08** — raw PDF (image) read visually: roster
   Peterson/Schaeffer/Butterfield/Snow/Bush-Chair and all motions transcribed
   faithfully; only the `♦♦♦` decorative glyphs OCR-garble (`OOO 066`) — cosmetic.
   A source date typo ("November 13, **2024**") is preserved = faithful.
2. **Council born-digital, 2024-05-13** — 8 "moved…seconded…passed unanimously"
   motions all in `all_votes`; ordinance/resolution text verbatim; source typos
   preserved. This is a township-era doc: "**Mayor Kelly Bush, Chair, presided**"
   (the township chair was styled "Mayor" — NOT the elected city mayor).
3. **City-era 5-0 roll + the one contested council motion, 2026-05-11** — source:
   *"The vote was 4-0, unanimous in favor with Council Member Colby abstaining from
   the vote."* → `all_votes`: `result="4-0 unanimous in favor Pass (abstain: Lorrin
   Colby Jr.)"`, `member="Lorrin Colby Jr."`, `vote="Abstain"`. The other rolls read
   `5-0` with only 4 councilmembers → confirms the **voting mayor** (Valdez);
   max council roll = 5.
4. **PC land-use rec (OAM case key), 2021-08-09** — raw vs repo: MSD "MEETING MINUTE
   SUMMARY" letterhead + attendance grid + OAM-keyed recommendations
   (`#OAM2021-000388`, `#OAM2021-000391` "recommend approval … to the Kearns Metro
   Township Council") captured verbatim.
5. **Elections — external cross-check** — Mayor Valdez 2025: `kearns_races.csv` =
   1,932 votes / 57.64% def. Tina Marie Snow 1,420 / 42.36% (margin 512 / 15.27%).
   Matches ABC4 Utah + Salt Lake Tribune reporting **to the vote** (Utah's first
   Hispanic mayor; Kearns' first directly-elected mayor). PC/council items are
   ground-truthed against their PMN source PDFs above.

## ⚠ Coverage — read this

- **Council text minutes on disk now begin 2018-07-09 (backfilled 2026-07-12).** The
  original build logged 2017-2023 township-era meetings (111 rows) in
  `minutes_unrecovered.csv` as "genuinely absent (only agendas + MP3 audio on PMN)."
  That claim was **INCORRECT** — written "Meeting Minutes" attachments *are* published
  to PMN body 5823 across the township era. The full body was enumerated (255 notices);
  **111 township meetings carry a Meeting-Minutes attachment, 85 were harvested**
  (2018-07 → 2023; 84 `.pdf` + 1 `.docx` via `textutil`; OCR where scanned) and carved.
  What genuinely remains unrecovered (41 rows now, each with an accurate reason):
  **25 township meetings 2017-01 → 2018-06** whose Meeting-Minutes attachment WAS
  published but whose file blob has been **purged from PMN's pre-~July-2018 file store**
  (`file_id` < ~450000 → 404 at `/pmn/files/`; the notice link is stale; absent from
  the Internet Archive too); **7 township meetings** with only agenda + MP3 audio (no
  minutes ever published); **9 recent meetings** not yet approved/posted. The
  `SOURCES.md` note and `minutes_unrecovered.csv` reasons have been rewritten to state
  this accurately. The council record is now complete back to 2018-07 (the pre-mid-2018
  remainder is a PMN file-rot gap, not an acquisition miss).
- **PC gap IS genuine.** 2/2 sampled PC 2017-2018 notices carry Agenda + Packet only,
  no minutes — the "approved PC minutes begin 2019-03" claim holds honestly.
- **CRA gap (honest).** The council convenes as the Kearns Community Reinvestment
  Agency in-recess (referenced in council minutes), but the CRA's own PMN body was
  not acquired → **0 CRA rows**. Genuine honest gap for a separate body.
- **Comments (honest zero).** Kearns publishes no written-comment archive (in-meeting
  3-min input + email to the MSD recorder; submit-only). `all_comments_clean.csv` is
  header-only by design — see `public_comments/AVAILABILITY.md`.

## Elections provenance — parsed from RAW SOVC (canonical file corrupt)

`kearns_races.csv` is **authoritative** and was parsed directly from the raw Salt
Lake County SOVC workbooks, NOT from the shared
`salt_lake_county/elections/slco_municipal_results_long.csv`, which is **corrupted
for Kearns**: 2019 is dropped entirely, and the 2025 `SheetNN → contest` mapping
merged other municipalities' candidates under "CITY OF KEARNS MAYOR." Kearns is
therefore intentionally omitted from the county `CITY_PATTERNS` and the county-grain
`election_result` federated tag for Kearns is unreliable. Logged in repo-root
`TODO.md`. The special-district decoys (Oquirrh Park Board of Trustees, Kearns
Improvement/Water District, Kearns MSD ballot) are excluded.

## The two validator WARNs (both benign)

1. `a.layout: missing README.md, CLAUDE.md, VERIFICATION.md` — **created in this
   pass** (this file + `README.md` + `CLAUDE.md`).
2. `f.tally[meeting_minutes]: named tallies` — most council motions are narrative
   tallies (unanimous rolls unnamed, only dissenters/abstainers named). The 2026-07-12
   township backfill added a handful of 2018-2023 minutes that print a **full named
   roll call**; those per-member Ayes/Nays are captured verbatim (e.g. the `2019-09-09`
   3-2 pass, the `2019-10-14` 2-3 fail), which is why contested-motion count rose from
   1 to 5. Expected; not a defect.

---
*Addendum policy: extend this file with a dated note whenever the data is repaired
or re-audited (e.g. after the 2017-2023 council back-catalog harvest).*

---

## Addendum 2026-07-16 — pmn_backfill promotion (CRA lit up + PC 2019-04-08)

The 3 documents recovered by the 2026-07-13 `pmn_backfill/` build were promoted into
the audited layer (backups: `_backups/2026-07-16-minutes-promotion/kearns/`; raw
copies sha256-verified against the pmn_backfill fetch log):

1. **CRA 2025-07-14** (PMN body 9273, file 1320109, APPROVED, scanned→OCR) →
   `meeting_minutes/minutes/2025/2025-07-14/2025-07-14_cra-meeting.md`, `body=CRA`.
   **5 motions extracted, all ground-truthed against source: 5/5 correct**
   (officers 5-0 Snow/Schaeffer; bylaws 5-0 Snow/Butterfield; Smith Hartvigsen
   counsel 5-0 Snow/Butterfield; 2025 calendar 5-0 Snow/Butterfield; adjourn 5-0
   Snow/Schaeffer). Item 5.E (procurement policy) correctly has no motion — none was
   made.
2. **CRA 2025-09-08** (file 1430807, born-digital; PMN-labeled DRAFT but the
   in-body certification says approved 2026-05-11) → same convention. **4 motions,
   4/4 correct** (July-14 minutes 4-0 Snow/Schaeffer; bylaws adoption 4-0
   Snow/Butterfield; code of conduct 4-0 Butterfield/Schaeffer; adjourn 4-0
   Schaeffer/Butterfield; Peterson excused — the printed "absent from the vote"
   clause is not emitted as a named row, matching the audited council layer's
   handling of the identical grammar).
3. **PC 2019-04-08** (file 502755, approved 2019-06-10, MSD letterhead) →
   `planning_commission/minutes/2019/2019-04-08/…`. **2 motions, 2/2 correct**
   (March-11 minutes approval, Wellman/Walton unanimous; recommend file #30882
   [PF/PI public-facilities zones] to the Township Council, Wellman/Walton
   unanimous). The un-voted "close the public hearing" motion (no vote printed) is
   not emitted — consistent with extractor behavior. **The 2019-04-08 row in
   `minutes_unrecovered.csv` was FALSE** (minutes were on PMN; filename lacked the
   "Minutes" token) — removed, 24 → 23 rows.

Both `all_votes.csv` files gained a documented trailing 14th **`provenance`** column
(`minutes` = audited primary; `pmn_minutes` = these 3 docs), read from a
`**Provenance:**` md front-matter line written by `convert.py` from a new manifest
column. Row-grain diff vs the pre-promotion CSVs: **additive only** (+9 CRA rows, +2
PC rows; 0 removed, 0 changed). Derived layers rebuilt (db 700 motions / 64 votes,
bodies Council 492 / PC 199 / CRA 9; referrals gained 3 medium Council←CRA subject
links to Ord 2025-O-06 creating the CRA; weeks 114 bundles; motions_std 501+199;
sources 803 docs). `validate_city.py`: **23 PASS / 3 WARN / 0 FAIL** (the +1 WARN is
the documented provenance extension column). Known cosmetic quirk carried forward:
"To recommend …" motions can classify as `Ceremonial` (the "commend" substring) — the
new PC m2 matches 5 pre-existing audited rows; normalization goes through
`motions_std.csv`.
