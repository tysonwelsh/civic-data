# Independent audit — Park City PC folded-era re-extraction (2026-07-19)
*(Method: audit-city-data SKILL. Auditor sandbox blocked the report write — persisted
verbatim by the orchestrator.)*

## VERDICT: B+
The re-extraction is faithful and well-reconciled. All 22 new contested motions are
verbatim-true to source (zero fabrication), the pre-2024 boundary is byte-identical
except the 6 documented recoveries, and db / motions_std / weeks / referrals reconcile
exactly. Two residual defects from a single un-fixed root cause knock it from A to B+:
1 silently dropped motion and 6 cosmetically-garbled result strings.

## Scope independently covered
13 folded-era meetings row-by-row/outcome-grep (2024-10-09 → 2026-06-24, avoiding the
fixer's 5 named folded meetings); completeness scan of all 162 meetings; all 22 new
contested motions; all 8 WARN rows; full pre-2024 byte-identity diff; db/motions_std/
weeks/+12 referrals.

## Findings
**F1 — [DATA LOSS · HIGH] One motion dropped on 2024-11-13.** Source lines 1755–1765
(2024-11-13_planning-commission-meeting.md): "Commissioner Johnson moved to CONTINUE
the agenda item and the public hearing to January 8, 2025, and amend Conditions of
Approval #13 and #16… Sigg seconded… passed with the unanimous consent." Absent from
all_votes.csv/JSON/parkcity.db/motions_std/referrals (distinct from the Dec-11
continuance, captured as m8). Source has 10 outcome-bearing MOTION blocks + 1
no-outcome adjourn; only 9 extracted. ROOT CAUSE: a stray page-number token ("1." on
its own line) between "The motion" and "passed"; folded_vote_window bridges blank
lines but NOT an intervening non-whitespace footer/page token. The fixer's 11-meeting
sample did not include 2024-11-13.

**F2 — [QUALITY · MEDIUM] 6 result strings garbled by the same cause.** Motion
captured but result truncates to bare `Approved` with garbled result_text:
2024-11-13 m5 ("passed with the 1"), 2025-06-25 m3 ("…3"), 2025-08-13 m4 ("…7"),
2026-01-14 m4 ("…8"), 2026-05-27 m6 ("…0"), 2025-04-02 m6 ("…D", watermark letter).
Non-corrupting: outcome=Pass/disposition=approve correct on all 6; "unanimous"
qualifier lost; motions_std blank tallies + vote_mode=unknown. Same root cause as F1.

**F3 — [confirmatory] 22 new contested motions all source-verified, 0 fabrication.**
Full rolls (2025-03-26 m5/6/8/9, 2025-04-09 m4), prose partials (2025-04-23, 05-28,
01-08, 07-23, 08-27, 2026-04-08/05-13/05-27 Strachan abstentions, 2020-03-11 Suesser),
repeated-prefix dissent (2025-11-12 m6 Johnson+Frontero; 2026-04-22 m2 Tilson+Shand
"No" on a deny-motion carrying 3-2) all verbatim.

**F4 — [confirmatory] The 8 WARN rows are honest partials** (names_mode=partial with a
printed numeric tally, majority unnamed — the documented reading). The other 12
partials are also faithful.

**F5 — [confirmatory] Pre-2024 boundary byte-identical except the 6 recoveries**
(net +6 rows confined to 2020-03-11, 2021-11-17, 2023-01-18, 2024-06-12 ×3).

**F6 — [confirmatory] Derived layers reconcile exactly.** motions_std 872=872;
parkcity.db PC 872 motions / 285 named rows = CSV (no silent UNIQUE-drop);
deny-carried disposition/outcome correct; referrals 95→107 = +12 confirmed,
4 spot-checked genuine.

**F7 — [out of scope] Pre-2024 count gaps** (2020-11-18, 2021-02-10, 2021-10-13,
2022-02-09, 2022-03-23) byte-identical to pre-fix, benign on inspection.

## Ranked fix list
1. [HIGH] Strip mid-sentence page-number/watermark tokens separating "The motion"
   from its outcome verb (clean_lines()/folded_vote_window). Recovers F1 AND repairs
   the 6 F2 results — one root cause. Expect PC 872→873.
2. [MEDIUM · doc] Correct the "0 mismatches" note in both CLAUDE.md files (the
   11-meeting sample excluded 2024-11-13).
3. [LOW] Confirm F7 pre-2024 gaps benign in a future full-corpus pass.

## Audit blind spots
Row-by-row ground truth on 3 folded meetings + outcome-grep on 13; the other ~27
folded meetings rest on the corpus-wide MOTION-count scan (cannot catch a motion whose
MOTION: marker was itself garbled — none seen, not exhaustively excluded). Referral
genuineness checked on the PC anchor side only. Council/RDA/HA reconciled by count.

**Urgent:** none. F1 is a single procedural continuance (0.1% of motions) — but it
falsifies the fixer's "0 mismatches" claim, so fix #1 + doc-correction #2 should land
before that claim is cited.
