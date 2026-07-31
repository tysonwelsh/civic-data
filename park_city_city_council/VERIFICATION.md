# Verification — Park City Council data repo

**Date:** 2026-06-26
**Method:** data-integrity numbers independently RECOMPUTED from disk (csv-aware Python). Election
winners externally cross-checked at build time (Park Record / certified canvass PDFs — see
`election_results/CLAUDE.md`).

## Summary table

| Dataset | Status | Recomputed | Notes |
|---|---|---|---|
| Minutes | **PASS** | 238 index = 238 disk = 238 JSONs | 2020–2026; **0 iCloud dataless files**; born-digital (CivicClerk) |
| Votes | **PASS** | 1,562 motions · 7,763 rows · 99 contested | `AYES:/NAYS:` roll-calls incl. split votes |
| — body | **PASS** | Council 1,503 / **RDA 46 / HA 18** motions | in-council Redevelopment Agency + Housing Authority recesses tagged |
| — mayor roster | **PASS** | no leak | Worel votes 2020–21 (councilmember) + exactly **1 properly-flagged Mayor tie-break** (2024-08-22, Res 16-2024, "Nay (Mayor tie-break)"); Dickey votes 2022–25 (councilmember), 0 in 2026 (mayor) |
| Elections | **PASS** | 11 races · 56 candidates · 308 precinct rows | **independently re-confirmed 2026-06-26** — 6/6 general-election winners match external sources (Park Record/KPCW/TownLift); 2025 mayor 7-vote recount verified. See `election_results/ELECTION_VERIFICATION.md`. Park City self-administers its elections |
| Comments | **PASS — PUBLISHED** | 459 genuine written (433 verbatim in minutes + 26 packet correspondence) + 1,055 speaker-log | all rows traced to source; 3 cross-source dupes dropped; speaker log kept separate (banner-flagged NOT comments) |
| Geo | **PASS** | city polygon (Summit + Wasatch straddle) + 13 precincts | true EPSG:4326; City Hall → INSIDE |

**Overall verdict: PASS.** Notably, Park City is one of the few cities with a GENUINE published
written-comment dataset (459 rows). (Comments were re-audited after two infra interruptions; final
output is deterministic + fully source-traced.)

## Detail
- **Minutes ↔ index ↔ JSON** reconcile exactly (238 each). 0 dataless stubs.
- **Votes:** 1,562 motions / 7,763 member-vote rows / 99 contested. `AYES:/NAYS:` lists parsed across
  line wraps + comma/"and" separators; tally-only "unanimous" → `names_recorded:false` (no guessing).
- **`body`**: in-council recess detection tagged the **Redevelopment Agency** (46 motions) and
  **Housing Authority** (18 motions) segments distinct from Council (1,503).
- **Mayor non-voting confirmed:** the mayor appears as a voter only via explicit, labeled tie-breaks
  (1 found: Worel, 2024-08-22); councilmembers-who-later-became-mayor (Worel, Dickey) vote only in
  their council years. No leak.
- **Elections:** winners externally confirmed at build; the 2025 mayoral race went to a recount
  (7-vote margin, both canvass PDFs saved) and is documented. Precinct sums reconcile to certified
  totals (2025 a few votes under, from late-cured/provisional ballots — documented).

## Remediation addendum (2026-07-02, audit Phase 1.6)
The vote figures above describe the ORIGINAL build and are superseded. Post-audit repairs
(`_audits/2026-07-02/report.md`; originals in `_backups/2026-07-02/park_city_city_council/`):
- **Votes re-extracted** with case-sensitive `RESULT:`/label regexes: **1,557 motions / 7,753 rows /
  98 contested** (Council 1,493 · RDA 46 · HA 18). The 10 removed "motions" were prose artifacts
  (public-comment `result: https://…` wrap, `excused.` sentence wrap, roll-call attendance "Excused"
  cells), each individually verified as non-motion text against its source file.
- **Mayor tie-breaks: 2, not 1** — Beerman 2020-06-25 (Ord 2020-31, 2-3 Fail) AND Worel 2024-08-22
  (Res 16-2024, 2-3 Fail). Both are now in `db/parkcity.db` (`vote.note='Mayor tie-break'`); the
  original db build had silently dropped both.
- **9 source clerk errors** (member in both AYES and NAYS/ABSTAIN of one motion) are now resolved
  explicitly and auditably in `db/vote_overrides.csv`; the db build fails loudly on any uncovered
  conflict and prints a full CSV↔db vote-row reconciliation (7,989 named rows = 7,980 inserted +
  9 merged override pairs + 0 excluded + 0 unresolvable).
- **weeks/ rebuilt** (203 bundles); weekly summaries now include the 459 public comments
  (previously all said 0 — built before comments were finalized).
- Referral layer rebuilt: 100 links (47 high / 30 medium / 23 low); `referral_overrides.csv`
  application ids re-verified by `app_key` (Studio Crossing shifted 209/160 → 207/159).

**2026-07-02 (3.1) council-vote validation:** shared validator installed as `meeting_minutes/validate_votes.py` and run — 7,753 rows / 1,557 motions; 0 schema/date/vocab defects ('Nay (Mayor tie-break)' ×2 = the documented extension), 0 malformed groups; 9 double-vote pairs all documented in `db/vote_overrides.csv`, 0 undocumented; tally-vs-counted 1,555/1,555; 0 unexplained mismatches.
