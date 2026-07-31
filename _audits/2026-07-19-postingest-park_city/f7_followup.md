# F7 follow-up — Park City PC pre-2024 count gaps: full-corpus confirmation pass (2026-07-19)

Ranked fix-list item #3 ("[LOW] Confirm F7 pre-2024 gaps benign in a future full-corpus
pass"). F7 flagged 5 pre-2024 PC dates whose extracted motion counts looked low relative
to the minutes; the original audit found them byte-identical to pre-fix output and benign
on inspection, and deferred a corpus-wide confirmation. This is that pass.

## VERDICT: ALL BENIGN — no missed extraction anywhere in the pre-2024 PC corpus.
Nothing was fixed. No extractor change, no derived-layer regeneration. PC invariants
unchanged (873 motions / 1,086 rows / 52 contested). `validate_city` = 24 PASS / 2 WARN /
0 FAIL (both WARNs pre-existing and documented). No files modified.

## Method
Two independent per-meeting metrics over all 104 pre-2024 PC meetings (date < 2024-01-01),
compared against distinct `motion_no` per date in `planning_commission/all_votes.csv`:

1. **Marker count** — `^\s*(MOTION|VOTE):` markers per minutes file (the audit's F7 method).
   Noisy: `MOTION:` markers routinely exceed emitted because adjournment / superseded /
   agenda-order motions carry a `MOTION:` label but no printed outcome (honestly dropped
   per the extractor's never-fabricate policy). Emitted count tracks **`VOTE:`** markers in
   the classic pre-folded grammar, not `MOTION:` markers.
2. **Outcome-sentence count** — the sharp metric: count of printed outcome sentences
   ("The motion … passed|failed|carried|denied|did not …") per meeting vs emitted motions.
   A real missed extraction would show **outcomes > emitted**.

**Result of metric 2:** outcomes == emitted for every pre-2024 meeting (delta +0) except
one -1 (2022-10-12, explained below — a watermark artifact in the audit regex, not the
data). **No meeting has outcomes exceeding emitted** — i.e. every printed outcome sentence
in the pre-2024 corpus became exactly one emitted motion. This is dispositive: no motion
with a recorded outcome was dropped.

## Per-date verdicts — the 5 F7 dates

- **2020-11-18 — BENIGN (honest no-outcome drop; 0 emitted is correct).** The sole
  `MOTION:` block is "Commissioner Thimm moved to CONTINUE the Park City Mountain Resort
  Base MPD Modification to December 16, 2020. Commissioner Suesser seconded the motion."
  followed immediately by "The Planning Commission Meeting adjourned at 10:35 p.m." No
  outcome sentence is printed — the motion was made and seconded but the minutes recorded
  no vote. Per the cardinal never-fabricate rule the extractor drops it; 0 emitted is the
  honest reading.

- **2021-02-10 — BENIGN (superseded/restated omnibus).** 7 `MOTION:` markers, 6 `VOTE:`,
  6 emitted. The extra marker is the King's Crown MPD-modification omnibus ("moved to
  forward a POSITIVE recommendation … concerning the substantive King's Crown Master
  Planned Development modification"): Planner Ward asked that it be split — "approve the
  modifications to Findings of Fact #112 and #113 in a separate motion and then forward
  the recommendation specific to the condominium plat." It was restated as the two voted
  motions that follow (approve FoF #112/#113; forward the plat recommendation). The
  omnibus carries no printed outcome → dropped. All substantive actions are captured.

- **2021-10-13 — BENIGN (fully classic).** 12 emitted = 12 `VOTE:` blocks = 12 outcome
  sentences; every voted motion (incl. the contested 4-to-1 on 316 Ontario with Suesser
  Nay) has a paired roll call. The single extra `MOTION:` marker is outcome-less
  (adjourn/superseded).

- **2022-02-09 — BENIGN.** 7 `MOTION:` markers, 5 emitted. The two extra markers are:
  (a) an initial "forward a NEGATIVE recommendation to the City Council" motion that was
  discussed ("The Commission discussed the motion…") and then **restated with findings**
  as the next motion (PL-21-04950 Mountain Ridge Lot 13), which carries the `VOTE:`; and
  (b) "Commissioner Kenworthy moved to adjourn. The meeting adjourned…". Both are
  outcome-less → dropped. 5 emitted is correct.

- **2022-03-23 — BENIGN.** 9 `MOTION:` markers, 7 emitted. The two extra markers are:
  (a) a procedural agenda-reorder ("moved to have Agenda Item 6.F. moved to the first item
  on the Regular Agenda") with no recorded outcome, and (b) "Commissioner Thimm moved to
  adjourn. The meeting adjourned…". Both outcome-less → dropped. 7 emitted is correct.

## Corpus-wide anomaly list (beyond the 5) and dispositions

- **Zero-emitted single-`MOTION:` meetings — 2021-06-16, 2021-09-29, 2021-12-15,
  2022-11-30, 2022-12-19 — ALL BENIGN.** Each has exactly one `MOTION:` block and it is
  "moved to adjourn / The meeting adjourned at …" with no outcome. (2020-11-18, above, is
  the sixth zero case and is a no-outcome CONTINUE.) 0 emitted is correct for all six;
  outcome-sentence count = 0 for each.

- **2021-06-09 — BENIGN.** emitted 7, `VOTE:` markers 8, outcome sentences 7. One `VOTE:`
  segment carries no outcome sentence (the mislabeled-marker guard case); emitted tracks
  the 7 real outcomes.

- **2022-06-15 — BENIGN.** emitted 6, `VOTE:` markers 3, outcome sentences 6. The
  sporadic folded grammar begins appearing mid-2022; three outcomes are folded into their
  `MOTION:` blocks and were correctly captured (emitted 6 == outcomes 6).

- **2022-10-12 — BENIGN (audit-regex artifact, not a data gap).** The lone -1 in metric 2
  (emitted 4, my regex found 3 outcomes). The uncounted motion is the contested Mountain
  Ridge negative recommendation whose printed outcome reads "The **ed** motion passed with
  a vote of 4-2" — a `-layout` watermark token ("ed") was injected between "The" and
  "motion", so the audit's flat-text regex missed it. The extractor's `clean_lines()`
  strips that watermark line before parsing, so the motion IS emitted with its full
  6-name roll call (Hall + Van Dine Nay). Confirms extraction is correct.

- **All "MOTION_markers > emitted" flags from metric 1** are resolved by metric 2's +0
  deltas: every excess `MOTION:` marker is an outcome-less adjournment, superseded/
  restated motion, or procedural agenda-order motion — never a motion with a printed
  outcome. The classic `MOTION:`=`VOTE:`+1 pattern that dominates 2022-2023 is the
  per-meeting adjournment motion.

## Conclusion
The pre-2024 PC corpus is clean. Every printed motion outcome is captured; the "low"
F7 counts are the extractor correctly refusing to fabricate outcomes for made-but-unvoted
motions (adjournments, restated omnibus motions, procedural agenda-order motions). No
extractor change and no derived-chain rebuild were warranted. F7 is closed as all-benign.
