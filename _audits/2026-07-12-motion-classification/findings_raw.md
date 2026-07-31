# T1.3 cross-city motion-classification audit — raw per-city findings
Accumulated as the 31 per-city ground-truth agents report. Synthesis → report.md.
Method: stratified ~10-18 samples/city (high-conf dispositions / NULL bucket / outcome-critical)
checked against source minutes + convention analysis of result_raw forms vs the tally regex.

## millcreek — FAIL (scoped: continue-class disposition + 1 tie outcome error)
- OUTCOME ERROR (1 real): PC 2024-08-21 m1 `3:3 Approved (Final Action)` stored Pass; minutes
  "did not pass" (3y/3n). Tie falls through to keywords; "Approved" is extractor-FABRICATED.
  Only 2 tie rows in city; the other (2514) also has defective result_raw (says Negative 3:3,
  truly positive 4:3 passed) but lands accidentally correct. → fix tie handling + note
  result_raw carriage words can be extractor-fabricated on ties.
- DISPOSITION continue-class: ~53 genuine continuances sit in NULL (native forms: "continue
  item 2.4", "continue application #30197", "continue file #", "continue Ordinance 26-36",
  "continue the discussion for one week" — article-less/object forms the keyword list misses);
  8 of 29 'continue' rows are FALSE (Millcreek PC "deferral agreement" sidewalk-exception
  idiom = an APPROVE with 'defer' in text); 3 continuances landed 'procedural' (2693/2673/2306).
  Net: continue class ~3x undercounted + 28% false. Also "to not recommend X" negation → should
  be deny (2 rows, currently NULL).
- Conventions: no date-fragment risk (0 rows); tally regex reads all forms; heavy tally-less
  "Pass (unanimous)" rows rely on carriage word (reliable). approve/deny/procedural sampling
  100% correct.

## sandy — WARN (tally-first net +15 but INTRODUCED 4 council errors; key design evidence)
- OUTCOME: ~20 PC flips all CORRECT (Legistar PassedFlag='Fail' artifacts on majority-Aye
  approved items — tally-first rescued them). BUT 4 council rows BROKEN by tally-first +1
  pre-existing: (1) m250 result_raw "3-0 Fail" — true roll 3-4, No block lost at a PAGE-BREAK
  (truncated tally); word Fail was right. (2) m161 "failed by a roll call vote of 5-2 with
  [dissenters]" — sandy narrative prints PREVAILING-SIDE-FIRST; 5=No. (3+4) m871/m879
  "3-2 Fail" with 2 Abstains — 3-2-2 FAILS under majority-of-full-council; abstains sink it.
  (5) m80 "1-1 Pass" pre-existing truncation (true 3-4 failed).
- DESIGN EVIDENCE: sandy council explicit Fail labels (minutes-derived) are RELIABLE and
  should beat a suspicious tally; sandy PC Fail labels (Legistar clerk artifact) are
  UNRELIABLE and tally should win. Word-vs-tally conflict resolution CANNOT be global —
  per-body/per-source reliability. Council conflicts (word=Fail, tally yes>no) = 4/4 word
  right. PC conflicts = ~20/20 tally right.
- DISPOSITION: sound; 1 minor (m674 "Table...indefinitely" → procedural). NULLs honest
  (PC=bare Legistar titles, 93.5% NULL — enrichment path: legistar_event_item.action_name
  carries the disposition signal, unused). Died rows keep proposed-action disposition ✓.
- UPSTREAM extraction defects to log: page-break-truncated roll calls (m80, m250);
  prevailing-side-first narrative tallies; PC result_raw retains misleading Legistar 'Fail'
  text on approved items.

## lehi — FAIL (disposition layer only; outcome layer PASS 17/17)
- OUTCOME: NONE wrong — incl. deny-motion 1:4 Fail, "Negative recommendation 5:0"=Pass,
  tie "FAILED 3:3"=Fail (word saved it). Outcome trustworthy as shipped.
- DISPOSITION root cause: lehi motion_text = the AGENDA-ITEM HEADER, not the moved sentence
  (only 191/2342 contain "moved to"). Three systemic modes: (1) "Table of Uses"/"Table
  05-030-B" code-amendment headers → FALSE table (≥35 certain of 187; 48 on Positive-rec
  results); (2) PC positive recommendations → procedural (358 of 536!) / negative recs ~0
  mapped to deny; (3) multi-motion items inherit one header (m765 actual table stored
  approve; m48 PC-narrative "recommend denial" bleed → false deny). NULLs are classifier-gap:
  256/640 contain "approv" (participle "approving" not in lexicon); 509/640 are
  "Consideration of..." headers. Fix priorities (a)-(d) in agent report.
- Conventions: regex reads all shapes; 0 date-fragment risk.

## park_city — WARN (isolated; 3 outcome + 2 disposition errors, 2 portable patterns)
- OUTCOME: (1+2) tally-less "Denied unanimous" → keyword 'den' → Fail, but BOTH are
  motions-to-deny/ratify-denial that CARRIED (should be Pass) — carriage words describing
  the ITEM invert tally-less outcomes for deny-class motions (tally path handles same
  semantics right: "Denied 3-1" → Pass ✓). (3) PC narrative "The motion failed 4-to-2" is
  MAJORITY-FIRST (4=No) → regex read 4 yes → stored Pass, truly Fail (m2152; also has 0
  vote rows despite named 6-member roll — upstream). Both mayoral tie-breaks verified ✓.
- DISPOSITION: "appeal of the CUP DENIAL" noun → false deny (2 rows,真 continue).
- NULL gap: 63/324 NULLs are "moved to continue <item> to <date>" (61 already
  outcome=Continued — mechanical recovery).
- Date-fragment check: "5-0 September 17, 2020" — tally first, regex correct ✓.

## vineyard — WARN (1 outcome error; dispositions 20/20 clean; NULLs honest)
- OUTCOME: m1336 PC "2:1 Denied (Final Action)"; minutes "THE MOTION FAILED TO PASS"
  (2 ayes insufficient under majority-of-body on small panel) — tally-first says Pass.
  Single row; needs override (no signal in string distinguishes it). Full-table scan: no
  other contradiction. Deny-that-passed semantics all correct.
- NULL recoverables: "MOVE <item> to next agenda/future meeting" ≈ continue (~10);
  adjourn typos ("AJOURN"), NOMINATE/CERTIFY → procedural.
- Bimodal result_raw: council prose ("Carried unanimously" — no tallies), PC tallies. Regex
  safe; pmn RDA backfill spot-checks clean.

## south_jordan — WARN (2 outcome errors — BOTH 3-3 ties stored Pass)
- OUTCOME: m1471 PC 2022-10-11 3-3 CUP ("The motion failed per the vote") stored Pass;
  m1697 PC 2025-03-25 3-3 stored Pass + recommendation='Positive' (poisons v_pc_divergence).
  Only ties in city; Fail count should be 4 not 2. → tie ⇒ Fail rule.
- DISPOSITION: 15/15 correct; systematic inflation: 117 "approve the agenda" motions →
  approve (should be procedural).
- NULLs honest (~126 appoint/nominate/amend-agenda procedural wordings; ~20 upstream
  carving fragments — 78 fragment texts city-wide, log upstream).
- Regex safe (adjournment times don't false-match).

## nephi — WARN (2 outcome errors; dispositions solid; NULLs honest)
- OUTCOME: (1) m265 council result_raw "0-1 Pass" — CORRUPT upstream tally (extractor
  captured only the Nay; minutes: passed 4-1) → tally-first flipped a passed motion to
  Fail. Word 'Pass' was right. (2) m1229 PC "Positive recommendation 2:2" tie → Pass
  (tie bug; minutes have no carriage — forwarded to council undecided).
- DISPOSITION: values correct; 2 approve/high from BLED narrative text (right by luck) —
  2022-PC terse format ("Motion: X Second: Y Outcome: Passed" with NO motion wording) is
  the risk zone; consider confidence demotion there.
- 95.4% of city is no-tally controlled strings ("Pass (unanimous)") — keyword fallback safe.
- Footer-bleed: present but carries NO disposition keywords — no flips found.

## === EMERGING CROSS-CITY PATTERNS (7 reports in) ===
P1. TIE ⇒ stored Pass (millcreek 1, south_jordan 2, nephi 1 = 4 errors): yes==no falls to
    keyword/default-Pass. FIX: tie → explicit carriage word if present, else Fail.
P2. Explicit carriage WORD vs decisive tally conflicts: word was RIGHT 5/5 in minutes-derived
    strings (sandy council 4, nephi m265 — corrupt/truncated/reversed tallies); tally was
    RIGHT ~20/20 in sandy PC (Legistar PassedFlag artifact — city-specific, fix in sandy fork).
    FIX (global lib): explicit carriage word (fail/failed/did not pass vs pass/carried) beats
    tally on conflict + print the conflict; sandy fork handles its PC specially. Hard guard
    must then exempt word-supported outcomes.
P3. Tally-less 'den' keyword inverts deny-motions-that-carried (park_city 2): "Denied
    unanimous" = the ITEM was denied = motion carried. FIX: in no-tally branch, 'den' should
    NOT → Fail when the motion text itself proposes denial (compose with disposition).
P4. Majority-first narrative tallies ("failed 4-to-2" = 4 No) — park_city PC, sandy.
    FIX: when a fail-word precedes/accompanies the tally, don't read tally as yes-first
    (word-priority P2 already covers the outcome; note for extractors).
P5. Disposition lexicon gaps (multi-city): "moved to continue <X> [to <date>]" + article-less
    "continue item N.N"/"continue <Ordinance|application|file> #" (millcreek 53, park_city 63,
    vineyard 10); participle forms "approving/adopting/authorizing" (lehi 256); "positive/
    negative recommendation" headers → approve/deny BEFORE procedural (lehi 358); "not
    recommend" → deny (millcreek); "approve/adopt the agenda" → procedural (south_jordan 117).
P6. Disposition false-positive guards: "Table <digit>/Table of Uses/Bulk" ≠ table (lehi ~35-83);
    "deferral agreement" ≠ continue (millcreek 8); "appeal of the ... denial" noun ≠ deny
    (park_city 2).
P7. Upstream extraction defects (log to TODO, separate from classifier): sandy page-break
    truncated rolls; nephi m265 lost 4 Yes rows; park_city m2152 zero vote rows; south_jordan
    78 fragment motion_texts; millcreek 2 fabricated tie result_raw labels.

## orem — WARN (3 hard outcome errors, all PC supermajority/tie; dispositions 15/15 clean)
- OUTCOME: m1053 "3:1 Denied (Final Action, motion failed)"→Pass (4-vote rule; 'failed' in
  string!); m1054 "3:1 Fail"→Pass; m988 "Negative recommendation 3:3" tie→Pass. 2 ambiguous
  "Positive recommendation 3:2" (city precedent: carriage Pass, forwarded rec = neutral —
  `recommendation` column misstates; adjacent-column defect). 2 pre-fix flips CORRECT (raw
  "Fail" was narrative bleed — tally saved them; NOTE counter-evidence for word-priority:
  orem 1057/1060 raw 'Fail' is FALSE, tally right!). NULLs honest (amend/appoint classes).
- Orem PC four-concurring-votes rule breaks simple-majority on 3:1/3:2 property items.

## logan — WARN (1 outcome error; ~50-61 continue undercount)
- OUTCOME: m49 "3-2 Fail (no names)" → Pass; minutes "Motion failed 3-2" with 3 NAMED nays
  (prevailing-first). Word right. (Also: those 3 nays never extracted — upstream.) Other 9
  flips all CORRECT incl. subtle ones: logan PC prints FORMULAIC "Approved: X-Y" even on 0-5
  defeats (m968) and result_raw "7:0 Denied" artifact over true "Approved: 7-0" (m918) —
  logan PC carriage/item words unreliable, TALLY right there (word-priority must use strict
  carriage words only: fail/pass, not approved/denied ✓).
- DISPOSITION: none wrong; NULL gap: ~50-61 sentence-form "moved to continue PC 20-022 to
  <date>" (mid-sentence continue not caught) — true continue ≈ 2x stored.

## st_george — WARN (3 outcome errors — all PC majority-of-membership/tie)
- m1829+m2310 "Positive recommendation 3:2 (failed)"→Pass ('failed' IN the string, tally
  overrode); m2010 "Positive recommendation 3:3" tie→Pass. Advertised prose-in-result risk
  DID NOT materialize: 59 distinct result_raw, regex 2765/2765 clean, 0 implausible pairs.
- 3 merged died-motion rows (178/316/1379: died/withdrawn motions collapsed into voted
  siblings — Died systematically invisible; m178 disposition=table from withdrawn part).
  UPSTREAM. m2457 mixed deny+approve → procedural/high (reclassify). NULL gaps: appoint (62),
  "continue Item N" PC form (11).

## west_jordan — WARN (5 outcome errors: 2 majority-first + 3 rec-ties)
- m276 "4-3 Fail" truly 3A/2N/2Abst failed; m631 "6-1 Fail" truly 1A/6N (worst: 1-6 loss
  stored Pass). WJ failed tallies INCONSISTENT order (usually yes-first "failed 3-4" ✓,
  sometimes majority-first). m990/991/992 "Negative recommendation 3:3" ties → Pass (source:
  "failed 3-3"). 25% of city's true Fail class wrong. Dispositions sound; deny semantics ✓.
- NULL gap: 10 "continue <Ordinance|Resolution> No. X to <date>". OCR tally-loss NIL (0 rows).
- Upstream: m412 lost 6 of 7 named votes (roll incl. Green:No — affects v_contested).

## taylorsville — FAIL (non-Pass class corrupted both directions; 57% recall)
- m130 "3-2 Fail" majority-first → Pass (truly 2A/3N). m895 tally-less "Denied (Final Action,
  unanimous)" on a deny-motion-that-CARRIED → stored Fail (item-fate inversion, mirror of
  park_city). m835 withdrawn ("Negative recommendation n/a")→Pass; m836/m842 died-no-second
  ("No recorded vote")→Pass; m887 no-quorum→Pass. BUT m688/m770 "No recorded vote" are TRUE
  Passes (m770 7-aye roll missed upstream) — 'No recorded vote'→Died would break those:
  UPSTREAM extractor must emit proper Died/withdrawn results instead.
- DISPOSITION: m654 "Table of Setbacks" citation → false table; m625 "Table...the Minutes" →
  procedural (minutes-keyword false-fire on a real table motion); m930 + ~6 "continue File
  #X" → NULL/procedural (continue undercounted 4x); m593 "moved to pass Resolution" → NULL
  ('pass' as approval verb missing).
- No date-fragment risk.

## murray — WARN (2 outcome errors in the tiny failure class)
- m535 "Motion failed: 3-2" nays-first → Pass (roll: 2A/3N — db's own vote rows agree!);
  m213 "The motion was not seconded" (bare phrasing, no fail keyword) → Pass, should be Died.
- DISPOSITION: none wrong. NULL gaps: 4+ "continue <item> to/for <date>"/"delay a decision";
  ~25 nominate/elect/appoint/confirm (annual officer elections) → procedural candidates;
  "(ayes)-(nays)" parenthetical tally breaks regex (keyword saved it).
- Zero false regex matches on dates (no matched number >7 city-wide).

## === REFINED FIX DESIGN (12 reports in) ===
OUTCOME_OF v3 (evidence-weighted):
 1. Continued/tabled/postponed → Continued; died/'no second'/'not seconded' → Died.
 2. STRICT carriage word: 'fail' (incl '(failed)', 'Motion Fails') → Fail; 'pass'/'carried'
    → Pass. Item-fate words (approved/denied) are NOT carriage. On word-vs-tally CONFLICT →
    WORD WINS (fixes sandy council 4, logan m49, wj m276/m631, taylorsville m130, murray
    m535, st_george m1829/m2310, orem m1053/m1054, nephi m265 = 15 errors), EXCEPT sandy PC
    (Legistar artifact — fork keeps tally-priority there).
    COUNTER-EVIDENCE accepted: orem m1057/m1060 raw 'Fail' is narrative bleed (word-priority
    re-breaks 2 rows) — net +13; handle those 2 via override/upstream note.
 3. No word: tally, tie → FAIL (fixes millcreek m2908, sj m1471/m1697, nephi m1229, orem
    m988, st_george m2010, wj m990/991/992 = 9 errors; re-breaks millcreek m2514 whose
    result_raw is upstream-defective = net +8).
 4. No word, no tally: if 'den' in res AND motion's disposition=='deny' → Pass (fixes
    park_city 2, taylorsville m895 = 3); else 'den' → Fail; else Pass.
 5. Known residuals needing override/upstream (NOT classifier-fixable): sandy m80 (corrupt
    word+tally), vineyard m1336 (2:1 majority-of-body), millcreek m2514, orem m1057/m1060
    (bleed 'Fail'), taylorsville m835/836/842/887 + m131 (extractor should emit Died),
    st_george merged died rows 178/316/1379, orem rec-column neutral-rec cases.
DISPOSITION_OF v2: adds — mid-sentence/article-less continue ("moved to continue",
 "continue <Item|File|Ordinance|Resolution|application> [#]N", "to the next ... meeting",
 "to next agenda", "delay a decision", "continuation"); participles approving/adopting/
 authorizing/granting; "moved to pass <Resolution|Ordinance>" → approve; "not recommend" →
 deny; "recommend denial"/"negative recommendation" priority before procedural; appoint/
 nominate/elect/confirm → procedural; "approve/adopt the agenda" → procedural. GUARDS —
 "Table <digit>/Table of (Uses|Setbacks|Bulk)" ≠ table; "deferral agreement" ≠ continue;
 "appeal of the ... denial" noun ≠ deny; minutes-keyword must not trump an explicit
 "moved to table" (taylorsville m625).
GUARD v2: tally↔outcome check exempts rows where a strict carriage word supports the stored
 outcome (word-over-tally cases print as review lines, not failures).

## slc — WARN (6 PC outcome errors — ALL upstream missed-aye-block extraction, not classifier)
- m2061/m2156 "0:1"/"0:1" false Fails: aye blocks in first-name-list / no-"voted"-verb forms
  never extracted (true 7:1, 8:1 Pass). m2130 PHANTOM motion (mid-roll "The motion passed."
  split one motion into two; fabricated 0:2 Fail). m2201 "0:8" scrivener double-nay blocks vs
  explicit "motion passed 5-3" carriage. m2045 2:2 stored Pass — chair TIE-BREAK Nay missed
  (true 2:3 Fail). m2239 "5:5 Approved" tie → Pass+deny (truly failed; item then TABLED).
- 4 of 25 stored Fails are false; all 4 zero-aye tallies are undercounts. The genuinely
  corrected close-tally Fails (4:5, 2:6, 3:5) all verified CORRECT.
- Dispositions 0 errors; NULLs honest (as characterized at build time). Regex clean.
- Fix: vote_overrides/re-extract for the 6; tie→Fail-unless-explicit-tie-break.

## draper — WARN (1 flip-to-wrong + 1 fabricated row, both upstream)
- m1267 "0-2 Negative Recommendation": 3 Aye rows never parsed ("Commissioners Fowler,
  Bingham, Squire, voted, 'Aye.'" form) — true 3-2 Pass; tally-first flipped correct→wrong.
  m1007 result misattached to a never-voted withdrawn motion ("to NOT continue" — negation
  also gives false continue/high). Near-misses: page-break-split Yes/No/Absent grids (2024+
  format) → corrupt 0-0/1-0 tallies + phantom Absent rows (m651/m692).
- NULL gap: 38/83 NULLs are "moved to continue <Ordinance|named item>" — continue recall 19%.

## ogden — WARN (1 outcome error upstream OCR; 2 table→procedural)
- m360 "2-2 Fail" derived from OCR-garbled roll ("VICE CHAm WIDTE") that dropped 2 ayes —
  truly carried 5-2. m370/m450 impossible 8/9-voter tallies (double-counted contradictory
  rolls) — outcome right; add impossible-tally lint. Ties m986/389/393 verified CORRECTLY
  Fail (tally-first beat "PASSED AND ADOPTED" boilerplate — design vindicated).
- DISPOSITION: m1495/m61 "MOVED TO TABLE the proposed appointment/proclamation" → procedural
  (appointment/proclamation PROC keywords outrank the table verb). NULL gaps: passive "BE
  DENIED" (3 — 'denied' NOT a substring of 'deny'!), lowercase "to continue until <date>" (4).

## cottonwood_heights — WARN (outcome clean; disposition systematic)
- TALLY_COVERAGE 0/1410 confirmed — word-form "Passed 4-to-1"/"Failed 3-to-2" tallies are
  UNPARSEABLE by the regex, which is accidentally PROTECTIVE: CH failed tallies are NAYS-
  FIRST ("Failed 3-to-2" = 2A/3N). If regex ever extended to N-to-M, every CH failure flips.
- Outcome 9/9 Fail/Died rows verified ✓ (keyword fallback has complete coverage of the 16
  extractor-normalized shapes).
- DISPOSITION: 'ratif' → procedural at high ×32 (substantive "Approving and Ratifying a Bid"
  = approve; one true TABLE m820); m687 merged approve+died-table-substitute blob → table;
  m91 "moved to pass Resolution" → NULL ('pass' verb missing). Continue class broken: 2
  stored vs ~24 true ("CONTINUE Project <CASE>"/"CONTINUE Resolution" forms; 22 in NULL).
- Upstream: 2024-01-02 portal/PMN duplicate doc pair (8 motions double-counted incl. a Fail);
  unextracted died substitute motion 2024-01-16.

## white_city — WARN (outcome faithful; Fail-vs-Died taxonomy + upstream)
- 6 of 7 plain-"Fail" rows are died-for-lack-of-second (extractor condensed result to bare
  "Fail" — classifier's no-second trigger can never fire) → should be Died. 1 genuine 2-3 ✓.
- Upstream: 7 died motions NEVER extracted ("motion dies/fails for lack of second" variants);
  m267 3 named Nays stored tally-only (single-dissenter-only handler); m569 4-1 contested
  vote stored bare "Pass" (invisible to v_contested). "4-1" can encode Abstain not Nay.
- NULL gap: "close the <meeting>" forms (~7-10) → procedural.

## west_valley — WARN (2 rec-tie outcome errors; continue class unusable)
- m2430 "Negative recommendation 3:3"→Pass (printed "FAILED"); m2472 "Negative rec 2:2"→Pass
  (truly 3Y/2N/3AB FAILED under majority-of-full-commission; also missed a Yes voter).
- Case-number false-tally risk CLEAR (0/2548). "Positive recommendation 0:0" synthesized
  voice-vote tallies → word fallback ✓.
- DISPOSITION: continue 93/94 wrong-or-NULL ("to continue <CASE#> to the <date> public
  hearing" — 60 NULL + 33 procedural); only "continue this item" fired.
- Convention: WVC council continuances get outcome=Pass (result "7-0 Unanimous Pass") while
  PC's get Continued — cross-city Continued counts undercount WVC council.

## holladay — FAIL (CLOCK-TIME TALLY BUG — introduced by the tally-first fix!)
- 8 wrong Fails (m72,179,233,281,289,299,316,388): recess/adjourn results "...passed with
  unanimous consent ... and the meeting recessed at 7:12pm" — regex read "7:12"/"6:20 pm" as
  yes:no and FLIPPED explicit 'passed' prose to Fail. These were the 6 'pass_should_fail'
  baseline rows — resolved the WRONG direction. Fail-class precision 2/10. +2 latent
  coincidental (hour>minute). FIX: exclude clock-times (\d:\d\d\s*[ap]m / after ' at ') from
  the tally regex + word-priority.
- m842 result truncated at "There was no second." (next sentence: "The motion passed
  unanimously" — Holladay scribe idiom) → false Died.
- DISPOSITION: m304 "ADOPT Ord...Table 13.100" + m795 "add STRs to the Table of Allowed
  Uses" → false table; m710/724/777/783 plat-condition boilerplate "defer the administrative
  review...to the Director" → false continue (4/4 'defer' rows wrong).
- Nay-first "FAILED with a vote of 5-to-0" (=0A/5N) — currently right via word; keep word
  priority. NULLs honest.

## herriman — WARN (1 salient outcome inversion; table class 100% false)
- m270 "failed with a vote 3:2" = WINNER-FIRST (2A/3N) → stored Pass; db's own vote rows
  contradict outcome. The only contested-fail council ordinance of 2021-09-08.
- DISPOSITION: ALL 6 table rows false ("Land Use Table"/"Table of Uses"/"table footnote"
  nouns); m803 "defer impact fees" → false continue.
- Upstream: 11 result_raw wrap-truncated; m280-282 narrative roll calls ("Watts, Shields,
  Smith voted aye...") have 0 vote rows — named dissent lost to v_contested.

## midvale — WARN (1 Died-as-Pass; negation deny miss; OCR roll dropout)
- m106 "died for lack of a second" but result_raw='Recorded (voice vote)' → Pass (voice-vote
  fallback). m1438 lack-of-second → Fail (should be Died; direction ok). Tie-break m70 ✓.
- DISPOSITION: m1439 "recommend to NOT approve rezoning" → approve/high + recommendation=
  'Positive' (feeds referral layer WRONG). Negation miss.
- NULL: 96/177 are "open/close the public comment section of the hearing" → procedural gap.
- UPSTREAM (material): OCR "Gouncil Member" roll-line dropout across 41 files — 45 vote
  lines dropped; 4 lost NAMED NAYS (m533 Brown, m537 Brown, m569 Glover, m681 Gettel) +
  tally undercounts (m422/801/783) — v_contested + margins misstated 2020-23. Tolerate
  Gouncil/Counci! variants in roll parser + rebuild.

## kearns — WARN (2 false Fails = 50% of Fail class; continue never fires)
- m596/m598 PC minutes-approval rows: "1-3" bled from NEXT agenda item title ("Phase 1-3
  Ordinances") into result ("1-3 unanimous in favor Pass") → Fail. True Pass. Upstream
  extractor bleed. 2 genuine 2-3 Fails verified ✓ (incl. "failed 3 to 2" correctly stored
  2-3 — kearns extractor normalized!).
- DISPOSITION: continue 0/689 fires (64/494/517 NULL; 600/604/629 "continue approval of the
  Minutes to..." → procedural via minutes token). m529 substantive land-use → procedural.
  Nominate-as-Mayor → NULL vs nominate-as-Chair → approve (SLC-tuning artifact).
- Upstream: named-roll harvest incomplete in the fresh 2018-23 back-catalog (m227 full
  5-aye roll → 0 vote rows; m610 named Nay not in vote table; 7+10 grep hits vs 6 captured).

## copperton — WARN (outcomes flawless; 1 continue false-positive; duplicate doc)
- m441 "defer to the County code" (substantive positive rec) → continue/high (25% of the
  tiny continue class). Good restraint verified: "continue the Emergency Declaration" and
  "continue to use <person>" correctly NOT continue — GUARD EVIDENCE for continue patterns.
- UPSTREAM: PC 2025-07-02 doc is a DUPLICATE (draft-vs-approved) of 2025-05-13 — all 6
  motions double-counted incl. the deny rec (deny class ×2 inflated; PC 51 not 57 motions).
- NULL gaps: 16 close-session forms; ~15 appoint verbs.

## emigration_canyon — WARN (outcomes clean 427/427 Pass genuine; continue class inverted)
- DISPOSITION: m67 "continue board assignments as assigned" (keep-assignments) + m71 "fees
  ...reduced, deferred, postponed" (staff directive) → false continue (2 of 3 high-conf
  continue rows); 7 textbook PC continuances "To continue file/application #NNNN to <date>"
  sit at NULL. Continue detection effectively inverted.
- "4-1 Pass" dissent-type ambiguity (Nay/Abstain/Recuse). Truncation cut a decision verb
  (m319 NULL).
- UPSTREAM: m89 recusal + m182 FULL five-name roll call never extracted (doc claim "3
  contested council motions" is wrong — there are 5).

## === ADDITIONAL FIX ITEMS (25 reports in) ===
F1. TALLY REGEX: exclude clock-times ("at H:MM(pm)", \d:\d\d\s*[ap]\.?m) — holladay killer.
    Do NOT extend to "N-to-M" word forms (CH nays-first — protective unparseability).
F2. Died keywords += "not seconded", "lack of a second" (white_city/murray/midvale forms
    reachable only where result carries the phrase; upstream fixes needed where condensed).
F3. DISPOSITION reorder: continue-verb + table-verb checks BEFORE _DISP_PROC (fixes
    minutes/appointment/proclamation tokens trumping explicit motion verbs — ogden, kearns,
    taylorsville). Keep "approve the minutes" → procedural (verb-form gate).
F4. table: require VERB form ("to table", "moved to table", "tabled", "lay on the table");
    never fire on "Table <digit>", "Table of <anything>", "<word> Table" nouns (herriman 6,
    holladay 2, lehi ~35-83, taylorsville 2).
F5. defer: replace bare "defer" with context forms ("defer action", "defer the item",
    "defer <obj> until/to <date|meeting>"); never "defer to the <code|County|authority>",
    "deferral agreement", "defer the administrative review", "defer impact fees" (4 cities).
F6. continue recall: fire on "moved/motion to continue <obj>", "continue <Item|File|
    application|Ordinance|Resolution|Project|case|hearing> [#/No.] X", "continue <obj> to
    the <date|next meeting>", "continuation", "delay a decision", "reschedule ... to";
    GUARD "continue to <verb>" (hold/use/allow — SJ COVID, copperton) and "continue the
    Emergency Declaration/board assignments as assigned" (keep-doing forms).
F7. deny: add "denied" (passive "BE DENIED"), "not recommend", "not approve" negations
    (millcreek, midvale, ogden). approve: add participles "approving/adopting/authorizing/
    granting", "to pass <Resolution|Ordinance>" (taylorsville, cottonwood, lehi NULLs).
F8. procedural: add "open/close the public comment", "close the <staff |open |Council |CDRA >
    meeting/session", "open the business portion", "reorder the agenda", "amend the agenda",
    "approve/adopt the agenda" (midvale 96, white_city, EC, copperton, murray, SJ 117).
    'ratify': move from PROC → APPR (cottonwood 32; keep minutes-approval → proc via
    'minutes' token). Appointments/nominations/officer elections: KEEP NULL (SLC design —
    honest; do not force).
F9. sandy fork: PC rows tally-priority (Legistar artifact); council rows word-priority.
F10. Per-row overrides/upstream queue (see per-city entries): slc 6, sandy 5, draper 2,
    ogden 1+lint, nephi m265, millcreek m2514, vineyard m1336, orem m1057/m1060+rec-col,
    taylorsville no-vote rows, white_city Died 6 + 7 unextracted, kearns m596/m598 bleed +
    roll harvest, midvale Gouncil dropout, herriman m280-282, EC m89/m182, holladay m842,
    copperton duplicate doc, cottonwood duplicate doc + merged motion, st_george merged died
    rows, SJ 78 fragments, wj m412.

## provo — FAIL (the largest single-city outcome damage: 14 wrong outcomes + 38 wrong-sign
##          high-conf dispositions)
- OUTCOME: **Provo prints failed/denied tallies MAJORITY-FIRST** — 11 council motions stored
  Pass that FAILED ("The motion was denied 7:0" = 7 opposed; "failed 6:1"; "failed 4:3") —
  all have named NAY-majorities in the vote table contradicting Pass. +2 PC ROA rows (m1243
  approve-motion failed 3:4 under headline "4:3 Denied"; m1340) + m1108 reverse ("0:6 ...
  continue" = 6 IN FAVOR; should be Continued). ~1/3 of provo's true failures mislabeled.
- UPSTREAM extractor bug BOTH DIRECTIONS: fail-regex includes `was opposed` (fires on
  "Councilor X was opposed" in APPROVED motions) → 5 false "N:M Fail" suffixes (m38,229,239,
  316,359 — accidentally Pass-correct under tally-first; would break under word-priority).
  FIX AT meeting_minutes/extract_votes.py:337 + re-extract BEFORE word-priority lands.
- DISPOSITION: 38 ROA rows approve/high where actual action was continue (28) or deny (10) —
  ROA motion_text is the applicant's REQUEST ("requests Concept Plan approval"); result_raw
  action headline (Approved/Denied/Continued) is the right source there.
- NULL 70% EXPLAINED: motion_text = agenda ITEM HEADER by design ("amending" 302,
  "authorizing" 47...); participle vocab recovers ~37%; ~218 PC request-texts classifiable
  from result_raw; ~136 honest. rec-column: m1555 Positive under "RECOMMEND DENIAL" headline.

## alta — FAIL (outcome layer: ~half of true failures misrecorded — ALL upstream 2021
##        narrative extraction)
- 4 flips (m58/66/73/99: named Aye/Nay lists + "The motion did not pass/failed" narrative →
  result_raw fabricated 'APPROVED'); m119 reverse (extractor caught only 2 Nays → "FAILED
  (0-2)" though minutes say "carried 3-2"); m65 never-voted motion → "RECORDED" → Pass.
  +2 genuinely failed motions MISSING from db entirely. 12 true failures, db right on 6.
  Root: alta 2021 narrative-grammar extraction (extends the known T3.1 line-wrap item).
- 'RECORDED (no vote line)' → Pass unconditionally (21 rows, ≥1 proven false).
- DISPOSITION: m53 header-driven approve over an actual TABLE motion; 0 table/deny exist.
  NULLs honest (ALL-CAPS agenda headers; MOTION sentence 2 lines below uncaptured).

## riverton — WARN (outcomes 0 errors incl. tie-break + winner-first Faileds all correct;
##            disposition false positives)
- "Table of (Commercial) Uses" → 10 of 41 table rows FALSE (7 true=approve, 2 true=deny,
  1 narrative bleed); "in Deference to/defer to the Table of Commercial Uses" → 2 false
  continue. ~12 "to CONTINUE Application PLZ-..." NULLs (inconsistent recall boundary).
- Winner-first "Failed 5-to-2" convention LATENT (unparseable "N-to-M" = protective; word
  carries outcome). m1323 "Passed 7-to-1" source arithmetic misprint (6A/1N).

## bluffdale — WARN (1 OCR-digit outcome error; header-bleed procedural block)
- m1248: OCR line numbers injected into "passed 4- 28 ~—to-1" → regex matched 4:28 → Fail
  (truly 4-1 Pass; the only row citywide where outcome contradicts named roll). Word-priority
  fixes. Mayor tie-breaks m411/m828/829 verified ✓.
- DISPOSITION: bare "minutes" PROC token collides with bled running header "...MEETING
  MINUTES Wednesday..." mid-motion_text → ~25 substantive motions (16 council approve incl.
  rezones; 9 PC positive recs) misfiled procedural at high. Fix: verb-anchor the minutes
  token / strip headers upstream.
- Prevailing-side-first "failed 3-to-2" (=2A/3N) — latent, word carries it.

## magna — WARN (1 fabricated Died; 42% council NULL from line-wrap truncation — upstream)
- m632 'Died (no second)' FABRICATED (source shows seconded, then no result sentence —
  truth unknown). Other 4 Died verified genuine. m699 supermajority failure ("3 to 2 in
  favor but failed — two-thirds required") correctly Fail via word ✓.
- DISPOSITION: PC "To continue <application> #X to <date>" frame: 0/21 → continue (13 NULL,
  2 FALSE approve via embedded 'approval', 6 procedural). m1211 "remove hospital from the
  table of uses" → false table.
- UPSTREAM (material): council motion_text truncated at first line-wrap (~338/899 end
  mid-phrase "moved to") → the 42% NULL rate is an extraction artifact; classification
  coverage depends on where the clerk's line wrapped. ALSO: named dissenters on split votes
  systematically uncaptured (33/41 N-M-tally motions have 0 vote rows; 4/4 spot-checks name
  dissenters in source) → magna falsely tally-only in v_contested_all.
- "Pass (dissent: X)" conflates Nay/Abstain; "4-1" can count an abstention as the 1.

## south_salt_lake — WARN (classifier fine; TWO FAIL-grade upstream extraction defects)
- OUTCOME: no carry/fail misjudgments (380/380 Pass genuine) BUT ~20 result_raw tallies
  corrupted by page-break/watermark-truncated PC vote blocks (db "2-0/1-0 Pass" vs true 7-0
  — sub-quorum 'unanimous' tallies impossible; internal validator circular). 8 DUPLICATE
  motions carved from DRAFT minutes embedded in the 2026-05-07 PC file (2026-02-19 +
  2026-03-05 double-counted).
- DISPOSITION: m298 "CONTINUE the Application for an Appeal of the Variance Application
  Denial" → deny/high (keyed on 'Denial' noun; continue class empty city-wide). "APPROVE
  the Agenda" (~46) → approve (procedural inflation, same as SJ).
- 83 'uncaptured' NULLs (22%) NOT honest: motion text exists in source (findings-list
  separation, "Move to forward", prose "moved to approve") — concentrated in substantive
  PC land-use motions.

## === FINAL TALLY (31/31 reports) ===
VERDICTS: FAIL 6 (millcreek, lehi[disposition], taylorsville, holladay, provo, alta) ·
WARN 25 · PASS 0.
OUTCOME ERRORS CONFIRMED: ~55 rows across 21 cities — classifier-fixable ~40 (word-priority
25+, tie→Fail 12, clock-time 8, disp-composed 'den' 3); upstream-extraction ~15+ (slc 6,
alta 6, draper 2, ogden 1, kearns 2, magna 1, bluffdale 1[also word-fixable], nephi 1,
SSL tallies, white_city Died-class 6).
DISPOSITION: systematic continue-recall gap in ~14 cities (~400+ recoverable rows);
table noun-trap in 6 cities (~60 false rows); 'defer' trap in 5 cities; header/PROC-token
collisions (bluffdale, taylorsville, ogden, kearns); negation misses; provo ROA 38.
The 2026-07-12 disposition/outcome layer NOT quotable for continue-class or per-city Fail
sets until v3 lands + rebuild.
