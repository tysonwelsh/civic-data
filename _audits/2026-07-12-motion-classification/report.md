# Cross-city motion-classification audit — 2026-07-12 (T1.3)

The gate audit required by TODO "AUDIT the motion-classification layer once it runs for
EVERY city + county" — run the same day the `outcome_of` tally fix + `disposition` column
rolled out repo-wide (T1.1). **Method:** 31 parallel per-city ground-truth agents, each
stratified-sampling ~10–18 motions (high-confidence dispositions / NULL-unclassified bucket /
outcome-critical Fail-deny-contested rows) against the actual source minutes, plus per-city
result-string convention analysis and, in many cities, exhaustive sweeps of the small Fail/
deny/tie classes. ~500 motions ground-truthed repo-wide. Raw per-city findings:
`findings_raw.md` (same directory).

## Verdict

**The T1.1 layer as shipped at midday was NOT quotable** for per-city Fail sets or the
continue class — the audit found ~55 wrong outcomes across 21 cities and systematic
disposition gaps in 14+ cities — **and the same-day v3 revision (below) fixed the ~40
classifier-attributable errors, verified row-by-row (25/26 checks, then 26/26).** The
remaining ~15 wrong rows are UPSTREAM extraction defects (corrupt result_raw / lost vote
rows) queued per-city in TODO.md; the classifier is honest about them (they carry the
corrupt strings verbatim).

City verdicts as audited (pre-v3): FAIL 6 (millcreek, lehi[disposition], taylorsville,
holladay, provo, alta) · WARN 25 · PASS 0.

## The four outcome root causes (and the v3 rules that fix them)

1. **Majority-first "failed N-M" tallies** (provo 11 rows!, sandy 4, wj 2, logan, murray,
   herriman, taylorsville, park_city PC): many Utah clerks print the PREVAILING side first
   in failure sentences ("The motion failed 4-3" = 3 ayes). Tally-first read them yes-first
   → flipped real failures to Pass. **v3: a strict carriage WORD (fail/failed/did-not-pass
   vs pass/carried) beats a conflicting tally** — in every minutes-derived conflict audited,
   the word was right and the tally corrupt (truncated, reversed, OCR-noised). Item-fate
   words (Approved/Denied) are NOT carriage. Exception: sandy PC's Legistar-synthesized
   "Fail" labels are PassedFlag artifacts — its fork keeps tally-priority for PC rows
   (evidence: PC ~20/20 tally right, council 4/4 word right).
2. **Ties stored Pass** (12 rows: sj 2, wj 3, slc 2, orem, st_george, nephi, millcreek,
   wvc 2): yes==no fell through to keyword-default-Pass. **v3: a tie FAILS** (word wins if
   present — preserves mayoral tie-break rows, all verified).
3. **Clock-times parsed as tallies** (holladay 8 rows — 80% of its Fail class was false):
   "the meeting recessed at 7:12pm" matched the tally regex as 7:12. **v3: clock-time
   patterns stripped before tally matching.** (Introduced by T1.1's tally-first change;
   caught same-day by this audit.)
4. **Tally-less item-fate "Denied" inverting deny-motions-that-carried** (park_city 2,
   taylorsville 1): "Denied unanimous" describes the MATTER; the deny motion CARRIED.
   **v3: tally-less 'den' composes with the motion's own disposition** (deny → Pass).

Supermajority rules emerged as a real convention (orem PC 4-concurring-votes; st_george PC
majority-of-membership): their failure rows carry "(failed)" in the result string, so
word-priority handles them without city-specific rules.

## Disposition: systematic gaps fixed in v2

- **continue recall was broken in ~14 cities** (~400+ recoverable rows; wvc 1→93,
  millcreek 29→76, draper 9→51): the SLC-tuned vocabulary missed article-less/object forms
  ("continue Item 2.4", "continue application #30197", "continue GPZ-3-2020", "moved to
  continue X to <date>"). v2 adds the frames with keep-doing guards ("continue to hold
  meetings" COVID motions, "continue the Emergency Declaration" — verified NOT firing).
- **"Table" noun traps** (herriman 6/6 false, riverton 10, lehi ~80, holladay 2,
  taylorsville 2, magna 1): zoning-code citations ("Table of Uses", "Table 05-030-B",
  "Land Use Table") fired the table keyword. v2 requires verb-anchored table forms.
- **"defer" traps** (5 cities): "deferral agreement" (a millcreek PC approval idiom),
  "defer to the County code", "defer impact fees", "defer the administrative review to the
  Director" all ≠ postponement. v2 uses context-anchored defer forms.
- **Verb-vs-token priority**: continue/table VERBS are now checked before the procedural
  token list (fixes "MOVED TO TABLE the appointment" → procedural, "continue approval of
  the Minutes to <date>" → procedural).
- **Negations** ("not approve", "not recommend", passive "BE DENIED") → deny; meta-verbs
  ratify/accept adopt their object's direction ("RATIFY the letter denying X" → deny).
- **Lexicon**: participles (approving/adopting/authorizing/granting), "to pass <Resolution>",
  "denied"; agenda/session mechanics → procedural ("approve the agenda", "open/close the
  public comment", "close the staff meeting"). 'ratify' moved procedural→approve
  (cottonwood: 32 substantive bid-ratifications). Appointments/nominations stay NULL by
  design (honest — the 5-class taxonomy has no slot).

## What stays honestly imperfect (upstream, queued in TODO)

The audit's most valuable byproduct: ~15 outcome errors + several corpus defects are
UPSTREAM of the classifier — corrupt result_raw or lost vote rows that no classifier can
repair. Queued per-city in TODO.md §"T1.3 upstream extraction defects", notably: slc 6 PC
missed-aye-block rows; alta 2021 narrative-grammar failures (~half its true fails); provo
`was opposed` cue (FIXED this session + re-extracted); midvale "Gouncil" OCR roll dropout
(4 lost named nays); SSL truncated PC vote blocks + 8 duplicate DRAFT-embedded motions;
kearns/magna named-roll harvest gaps; white_city Died-class + 7 unextracted died motions;
copperton + cottonwood duplicate documents; st_george merged died motions; draper page-break
grids; herriman narrative rolls; EC full-roll-call miss; known single rows (vineyard m1336,
millcreek m2514, orem m1057/m1060, sandy m80, taylorsville no-vote rows, magna m632).

## Verification of the v3 rebuild

- Unit tests: 37/37 outcome cases (every audited error + SLC regression suite), 45/45
  disposition cases after two pattern fixes.
- All 31 city builds INTEGRITY OK; the refined guard reports **38 word-over-tally review
  rows across 14 cities** — exactly the audited majority-first/corrupt-tally population.
- Row-level battery: 26/26 audited error rows verified flipped to the ground-truth value
  (or preserved where already right); sandy's 20 PC Legistar artifacts remain correctly
  Pass while its 4 council word-fixes landed.
- Full `rebuild_derived.py --all` re-run; federated cities.db re-verified (see TODO status
  notes).

## Residual limitations (documented, not defects)

- Word-priority makes 2 orem rows (m1057/m1060, narrative-bleed "Fail" in result_raw) and
  1 millcreek row (m2514, fabricated tie label) wrong until their upstream extraction is
  fixed — net vs v2: ~+40 correct rows.
- Vineyard m1336 (2:1 under a majority-of-body rule, no distinguishing signal in the
  string) needs a per-row override mechanism or upstream re-extract.
- Cottonwood's "N-to-M" word-form tallies are deliberately NOT parsed (its failed tallies
  are nays-first; unparseability is protective — outcomes ride the reliable Passed*/Failed*
  words).
- `recommendation` (legacy field) still keyword-derived; the disposition∘outcome cross-check
  prints its inconsistencies per city (deferred reconciliation, tracked in TODO item 1).
