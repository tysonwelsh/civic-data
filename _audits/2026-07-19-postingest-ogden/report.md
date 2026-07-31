# Post-ingest audit — Ogden Planning Commission 2020–2023 backfill
*(Audited 2026-07-19, post the 63-meeting gap recovery; method: audit-city-data SKILL.
Auditor agent's sandbox blocked the report write — persisted verbatim by the orchestrator.)*

**Scope:** the 63 newly-ingested PC meetings 2020–2023 + the derived layers they touch.

## VERDICT: PASS (grade A−)

The backfill is faithful to source and internally consistent. Transcription similarity
0.999, motion inventory reconciles file-by-file, every vote correction is correct and
source-cited, every tally mismatch is a genuine source defect handled per policy,
db + motions_std reconcile, roster is plausible. ONE isolated extraction defect
(9 lost attributions on a single motion; tally/outcome still correct) plus two minor
doc/labeling items. Nothing blocks use of the data.

## Findings by severity
- LOW: 1 data-loss defect (F1)
- LOW: 1 doc drift (F2)
- LOW: 1 provenance-labeling observation (F3)
- INFO: 1 no-defect note (F4)

### F1 — [LOW] Missed named roll-call: 2020-05-06 motion 9 (9 lost attributions) — REQUIRES ATTENTION
Source fully names the roll (8 aye + 1 nay) but the extractor recorded it TALLY-ONLY.
- Source (raw p.5): "…passed 8-1 **wit** Commissioners Blaisdell, Boykin, Garner,
  [pg.5 break] Graf, Sandau, Schade, Stoker and Southwick voting aye and Commissioner
  Safsten voting no."
- Root cause: clerk typo'd "with" as "wit"; the anchor `with Commissioners … voting aye`
  didn't match → tally-only fallback. Mid-roll page break compounds it.
- Isolated/bounded: the ONLY 2020–2023 motion where a numeric-N:N result has zero named
  members; "wit Commissioners" occurs exactly once. Tally (8-1) and outcome correct.
  Markdown transcription faithful (typo preserved verbatim).
- Fix: tolerate one-char corruptions of "with" (wit/wth/w ith) in the anchor, or trigger
  named-roll parsing off `Commissioners <names> voting aye|no` independent of "with".
  Post-fix expected: AYE = Blaisdell, Boykin, Garner, Graf, Sandau, Schade, Stoker,
  Southwick; NAY = Safsten.

### F2 — [LOW / doc drift] planning_commission/CLAUDE.md appointment cross-check stale
Says "14 of 16 roster commissioners … 2 not matched (Shinoda, Shale)"; live validation
says 19 roster / 15 confirmed / 4 not matched (Castillo, Wright, Herman, Shale) —
Shinoda now confirmed. Sentence predates the 3 recovered early-2020 commissioners
(pre-floor appointees, expected honest non-matches). Root CLAUDE.md already correct.

### F3 — [LOW / observation] Recovery channel not distinctly tagged in provenance
All 988 PC db motions carry provenance='minutes'. The 63 recoveries came from a NEW
channel — DocumentCenter unofficial-draft minutes (60), packet carves (2), one .docx —
indistinguishable from audited primary (unlike council's pmn_minutes). Approval is
verified downstream so trust is high, but a provenance='minutes' filter treats
draft-sourced recoveries as audited primary. Consider a doccenter_draft/packet_carve
tag. Not a data defect.

### F4 — [INFO] Disposition NULLs are honest
The 31 disposition-NULL PC motions are genuinely ambiguous (nominations, GP-consistency
findings, agenda re-ordering) with complete text — honestly unclassified.

## Verified clean
- Transcription (12 meetings incl. both packet carves 2020-04-15 & 2021-11-03, the
  2022-09-07 .docx, ≥1/yr): 0.999 similarity vs raw (delta = provenance header).
- Motion inventory (all 85 files): exact match except the 2 same-date WS siblings (benign).
- 6 vote_corrections: snippet verbatim in each markdown; each correctly applied
  (2020-03-04 m7 4:4, 2021-11-03 m3 3:5, 2022-03-02 m4 2:4 & m11 4:1, 2023-08-02 m8 8:1,
  2023-12-06 m6 3:6).
- Approval chains (6): confirmed at following-meeting source — 2020-02-05, 2020-05-06,
  2020-11-04, 2021-12-01 (exact "three aye and five no"), 2022-02-02, 2023-05-03.
- 6 clerk date-typo re-datings: all verified against approval batch + following meeting.
- 8 tally mismatches: all genuine source defects (double-printed names 2020-03-04 m11
  Graf / 2020-07-01 m9 Stoker; clerk-omitted aye 2020-09-02 m11, 2020-12-02 m8,
  2021-01-20 m7, 2021-08-04 m8, 2023-09-06 m6; printed list vs stated tally 2023-05-17
  m1). Correctly handled per policy.
- db reconciliation: PC 988 motions / 4,755 votes, CSV == db; council 197 pmn_minutes
  rows intact.
- motions_std tally cross-check (528 numeric rows): 0 real mismatches (single flag = F1).
- Roster: 3 new commissioners bounded to Jan–Mar 2020; spans consistent.
- Structural invariants: 0 double-votes, 0 carried-with-zero-ayes, 0 over-roster rolls,
  0 off-roster members.
- Contested: 149 all-years / 114 in 2020-2023 — reconciles with "+95 newly visible".

## Audit blind spots
- db referral/application regroupings (Franklin Street re-key, Ogden Bend force-link)
  not re-verified — out of scope.
- weeks/ + cities.db federation not re-checked (separate rebuild steps).
- Row-by-row roll verification covered ~18 motions + count-level on all 85 files; the
  non-contested Pass majority verified at count/inventory level.

**Immediate attention:** F1 only — the 2020-05-06 m9 "wit"→"with" parser fix
(9 attributions recoverable). F2/F3 optional tidy-ups.
