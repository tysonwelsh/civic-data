# Full TODO triage — 2026-07-31 publication-readiness review

Every open item (and open sub-item) in TODO.md, verified against the repo/gov.db by 8 parallel
agents (read-only). 245 rows. Verdict key: fix-before-publish | fix-soon-after | backlog-ok |
close-as-done (already landed, tick it off) | drop (not work — reclassify or delete).
Companion synthesis: `report.md` in this directory.

Summary: 10 fix-before-publish · 24 fix-soon-after · 124 backlog-ok · 62 close-as-done · 25 drop.
Verified status: 125 real-open · 61 stale-already-done · 28 not-an-issue · 20 partially-done · 11 unverified.


## Fix BEFORE publish (10)

### TODO.md:410 — (i) caveat rows for the non-city tier — SEEDED 2026-07-25 AND NOW STALE for utah_county and weber_county (NEW, not recorded anywhere)
*real-open · relevance: blocker · effort: S · section 43-560*

The caveat table is the mechanism CLAUDE.md advertises so 'mis-comparisons surface on every row' — and two of its rows now assert the opposite of the data. gov.db caveat utah_county/vote-ceiling still reads '~1,460 roll-call motions and ~4,000 member-vote rows are lost to two extractor bugs … BLIND to every divided Board vote after 2018 (3 Fail motions in 10,089). Do not read its post-2018 contested rate as real. Fix queued in TODO.md' — but item (c) landed 2026-07-25 and the db now holds 11,218 motions / 4,705 votes / 84 contested with named divided votes in every year (2019:9, 2021:11, 2025:6, 2026:6). caveat weber_county/tally-only-partial still reads '21 minutes documents are image-only copier scans never OCR'd, so ~198 motions / ~590 votes / 37 resolutions are absent' — item (d) OCR'd all 21 on 2026-07-26 and the db/file layer confirm the post-fix figures (4,404 motions, 12,585 votes, adopted_instruments.csv 844 rows). The caveats were seeded on 2026-07-25 and never refreshed after the 07-26 repairs. Result: a researcher is told, on every row, to distrust data that is now correct. Fix is a text edit in scripts/build_cities_db.py plus a re-federation run.

### TODO.md:491 — TIER 4 doc drift "✅ BATCH CLEARED" — root CLAUDE.md's utah_county bullet is STILL stale and actively warns researchers off correct data
*real-open · relevance: blocker · effort: S · section 43-560*

The TIER-4 note (line 504) claims utah_county's ceiling was corrected 'in all three places' including 'root CLAUDE.md:328'. utah_county/CLAUDE.md IS correct (line 13 headline '11,218 motions / 4,705 votes / 84 contested'; repair record db/REPAIR_2026-07-25.md). But root /Users/tysonwelsh/civic-data/CLAUDE.md:356–363 still reads '⚠ The repo's vote layer does NOT yet reflect that … ~1,460 roll-call motions and ~4,000 member-vote rows are lost … blind to every divided Board vote after 2018 — do not read its post-2018 contested rate as real. Fix queued in TODO.md.' gov.db contradicts every clause (named divided votes in 2019–2026, contested 84). Root CLAUDE.md is the first document any outside researcher or LLM reads, so this single stale paragraph makes a repaired entity look untrustworthy — the closure note for TIER 4 is wrong on this item. Same paragraph family: root CLAUDE.md:355 'County motions have NULL disposition (not yet computed)' is also wrong for two counties (see line 552 row).

### TODO.md:552 — Disposition column — salt_lake_county (and summit/utah/weber/wfrc) still NULL, uncaveated and mis-described in root CLAUDE.md
*real-open · relevance: high · effort: M · section 43-560*

Measured in gov.db: disposition is non-NULL for city 44,839/49,172, cache_county 2,949/3,388 and mag_mpo 577/635, but 0 for salt_lake_county (0/4,857), summit_county (0/3,402), utah_county (0/11,218), weber_county (0/4,404), wfrc_mpo (0/324) and ut_state (0/1,208). No caveat row anywhere mentions disposition except summit_county/vote-ceiling; root CLAUDE.md:355 says flatly 'County motions have NULL disposition (not yet computed)', which is false for cache and mag and silent about wfrc. Since CLAUDE.md points researchers at `disposition` for approve/deny rates and 'PC said deny → Council approved', anyone running that query across gov.db silently gets cities + 2 entities with no signal that the rest are excluded. The cheap pre-publish fix is a caveat row per affected entity + a corrected root line (S); computing disposition in salt_lake_county's Legistar-based build_db.py is the M-sized part.

### TODO.md:1057 — [DEBT] midvale — mis-dated duplicate meetings from Revize `M DD YY` filename-parse bug (date-collision class)
*real-open · relevance: high · effort: M · section 995-1124*

CONFIRMED AND UNDERSTATED — this is the biggest find in the range. All three filed council pairs reproduce in gov.db (2023-11-07 5 vs 2023-01-17, 2020-12-01 5 vs 2020-01-21, 2022-11-08 4 vs 2022-01-18), and /Users/tysonwelsh/civic-data/midvale_city_council/meeting_minutes/minutes/2023/2023-11-06/2023-11-07_city-council-regular-meeting.md line ~20 reads 'JANUARY 17,2023' with source filename 'CC Minutes 11723001.pdf'. BEYOND THE FILING, a repo-wide read-only detector (group_concat of full motion_text per meeting, self-joined on identical signature + different date) found MORE instances of the same class: (i) a FOURTH midvale pair the entry misses — PLANNING COMMISSION 2023-11-01 ≡ 2023-01-11, file 'minutes/2023/2023-10-30/2023-11-01_planning-commission-regular-meeting.md' whose own text reads '11th Day of January 2023' (source '11123 Approved PC Minutes.pdf'); (ii) magna PC — /Users/tysonwelsh/civic-data/magna_city_council/planning_commission/minutes/2023/2023-10-12_planningcommission_1032545.md is the SEPTEMBER 14, 2023 meeting (dated by approval date), duplicating 2023-09-14, 4 motions; (iii) weber_county — legislative/minutes/2021/2021-06-01_commission.md is byte-for-byte identical in body to 2021-05-11_commission.md (both 14,670 bytes) and its own text reads 'Tuesday, May 11, 2021' — 13 motions double-counted and the real 2021-06-01 meeting absent; (iv) holladay — minutes/2025/2025-04-28/2025-05-01_city-council-meeting_1282121.md (PMN file 1282121) contains 'Thursday, May 15, 2025' minutes, identical body to the 2025-05-15 record, 3 motions. So ~20+ motions across 4 entities are double-counted under WRONG dates: an outside researcher asking 'what did Midvale/Holladay/Weber decide on date X' gets another meeting's business, which is precisely the wrong-answer test. The entry's own prescription (a date-collision detector) is right and the query above is a working starting point; effort is M because each hit needs source confirmation before removal.

### TODO.md:1083 — [DEBT] (c) gov.db staleness + root CLAUDE.md quoting pre-federation counts — staleness FIXED, but the doc numbers landed WRONG
*partially-done · relevance: high · effort: S · section 995-1124*

Two halves, opposite verdicts. STALENESS: closed — gov.db (mtime 2026-07-29 03:01) matches every per-entity county db exactly (utah_county 11,218 motions/4,705 votes · weber 4,404/12,585 · cache 3,388/12,560 · summit 3,402/605 · salt_lake_county 4,857/8,142), so nothing is unfederated today. DOC UPDATE: done but WRONG. Root /Users/tysonwelsh/civic-data/CLAUDE.md:162-166 now says 'county 27,376 motions', '39,237 county member-votes', 'motion_std 77,507'; the shipped gov.db returns 27,269 / 38,597 / 77,400. The deltas are exactly -107 motions / -640 votes / -107 motion_std — i.e. the cache_county h3 de-duplication recorded at TODO.md:327 ('motions 3,495 → 3,388 (−107) · votes 13,200 → 12,560 (−640)'), which landed AFTER those figures were written and was never propagated. TODO.md:420 and TODO.md:1086 carry the same stale numbers; /Users/tysonwelsh/civic-data/HANDOFF.md:110,157 are staler still (24,346 / 35,318). This matters for publication because CLAUDE.md is the researcher-and-LLM-facing orientation doc and its headline row counts do not reconcile with the database being shipped — the first thing a careful user does is a COUNT(*). The doc edit is minutes of work; the entry's other candidate (a staleness gate in validate_entity.py) is separate and can stay backlog.

### TODO.md:1300 — Phase-4 follow-up (E) small — logan CLAUDE.md 'North Logan RCV' aside appears WRONG
*real-open · relevance: medium · effort: S · section 1125-1557*

CONFIRMED wrong: cache_county/elections/CLAUDE.md:41-45 states the county canvass contains no RCV tabulation ever and that North Logan 'never used RCV (held plurality primaries 2021/2023/2025)', while logan_city_council/election_results/CLAUDE.md:11 and :183 plus logan_city_council/recon.md:235 tell readers Nibley AND North Logan used RCV; election_results_by_contest.csv shows North Logan 2021 as an ordinary plurality At-Large contest — a factual error in a published city doc, fixable in one edit.

### TODO.md:1304 — Phase-4 follow-up (E) — county motion disposition layer (claimed 'all county motions NULL — extend classifier')
*partially-done · relevance: high · effort: M · section 1125-1557*

The premise is now HALF FALSE and the half-done state is the actual hazard: `SELECT city, SUM(disposition IS NOT NULL) FROM motion` gives cache_county 2,949 classified (approve 1,405 / procedural 1,403 / deny 109 / continue 19 / table 13) and mag_mpo 577, but salt_lake_county, summit_county, utah_county, weber_county, wfrc_mpo and ut_state are ALL at 0 — so a researcher running the documented `disposition='deny'` pattern across the county tier silently gets cache-only results and would conclude the other counties never deny anything; no caveat row covers this (the only disposition-adjacent caveat is summit_county/*/vote-ceiling), and root CLAUDE.md still asserts the blanket 'County motions have NULL disposition', which is itself now wrong.

### TODO.md:1928 — Wave closure claims "search-layer reconciliation exact" — but 935 recovered pmn_backfill minutes are excluded from fts_minutes
*real-open · relevance: high · effort: M · section 1921-2158*

The section header (TODO.md:1928) closes the 13-city promotion wave with "search-layer reconciliation exact". Verified against gov.db (built 2026-07-29 per build_info): `SELECT count(*) FROM fts_minutes WHERE path LIKE '%pmn_backfill%'` = 0, while `SELECT count(*) FROM document WHERE doc_type='pmn_minutes' AND has_text=1` = 935 (provo 391, murray 80, vineyard 80, herriman 72, west_jordan 60, orem 38, holladay 27, midvale 25, magna 20, ogden 19, cottonwood_heights 16, nephi 16, park_city 16, south_jordan 13, west_valley 13, …). Root cause is a doc_type filter in /Users/tysonwelsh/civic-data/scripts/build_search_layer.py:642-644 — `WHERE doc_type IN ('minutes','plan','advisory_opinion','statute')` silently drops the `pmn_minutes` doc_type added at line 506, with no comment explaining the exclusion (unlike the two documented exclusions right below it). Per-city proof that whole recovered eras are unsearchable: of the distinct `motion.source_file` values with pmn provenance, 0 of 4 (alta), 0 of 24 (midvale), 0 of 16 (magna) and 0 of 67 (herriman) appear in fts_minutes (white_city is the exception, 26/26, because its docs were promoted into planning_commission/minutes/). This directly contradicts what the docs promise: /Users/tysonwelsh/civic-data/CLAUDE.md advertises fts_minutes as "full minutes text across cities + counties + MPOs" and /Users/tysonwelsh/civic-data/cities_db_SCHEMA.md:128 says "full text of all 6,466 minutes markdown files" (also a stale count — actual 13,886). An outside researcher running the advertised ADU/density keyword sweep gets systematically undercounted per-city results and misses entire recovered date ranges, so at minimum the doc claim must be corrected before publish; the full fix (index pmn_minutes with dedupe against promoted duplicates, e.g. the millcreek OCR-probe copies) is a session of work.

### TODO.md:3413 — [GATED] NO VERSION CONTROL — put the repo under git (private, decoupled from publishing)
*real-open · relevance: blocker · effort: S · section 2783-3495*

Confirmed there is no .git directory (only .gitignore). AND the pre-worked .gitignore is STALE in a way that will break the very first attempt: line 21 ignores '/cities.db', which since the 2026-07-20 rename is a 6-byte SYMLINK, while the real 1,644,048,384-byte gov.db at repo root is NOT ignored — a naive `git add -A` stages a 1.6 GB blob, over GitHub's 100 MB per-file hard block (the .gitignore comment still says '392 MB', also stale). A second offender exists: draper_city_council/packets/text/2020-05-28_PlanningCommission_item1820_att1624.txt is 109,971,194 bytes. Measured prospective tracked set = 2.04 GB / 59,978 files, not the '~800 MB' the entry assumes. No real secrets found outside .env (the only 'sk-ant-' hit is a placeholder in a print statement at slc_city_council/public_comments/vision_extract.py:384; the two real .env files at slc_city_council/{meeting_minutes,public_comments}/.env are covered by the bare '.env' pattern).

### TODO.md:3443 — [GATED] Publish to GitHub as its own repo, linked from municipalsky.com
*real-open · relevance: blocker · effort: M · section 2783-3495*

This item IS the owner's stated goal, so it is a blocker by definition. Beyond the two >100 MB files and the stale .gitignore documented on line 3413, one thing the entry never mentions and I verified absent: there is NO LICENSE file at repo root (ls shows 16 top-level .md files, README.md present, no LICENSE/COPYING) — an unlicensed public research corpus is legally ambiguous to cite, redistribute, or train on, which directly undercuts 'a research resource'. Decide data license (e.g. CC0/CC-BY for the data, MIT/Apache for scripts) before first public push. Also settle the entry's own open question of whether the 100 per-city db/*.db files ship (largest is sandy.db at 5.4 MB — all comfortably under limits, so tracking them is viable).


## Fix soon after publish (24)

### TODO.md:406 — TIER 3 residual — mag_mpo drops printed divided tallies from result_raw (worse than filed: one INVERTED outcome + one missing motion)
*real-open · relevance: medium · effort: M · section 43-560*

Verified at source vs gov.db and the defect is larger than the entry states. Source strings (grep over mag_mpo/legislative/minutes) show 7 divided results; the db stores 2 truncated ('The motion passed with 18 yes' where 2014-09-04 prints '18 yes, 3 no (Mayor Pengra, Mayor Wall, and Mayor Miller), Mayor Clyde abstained' — cardinal-rule-2 verbatim violation), 1 truncated at the comma (2015-08-06), 1 full, and MISSES two entirely: 2014-09-04's Tier-3 gasoline motion ('Motion passed with 20 yes and 1 no (Mayor Miller)' — the db holds only 3 motions for that meeting) and, most seriously, 2015-11-05 where the source reads 'Mayor Chris Pengra moved to strike SUGGESTED RPC MOTION 1 … Motion failed with 10 yes and 12 no votes by [12 named mayors]' while the db stores motion_no 4 as 'approve SUGGESTED RPC MOTION 1' / result 'The motion passed' / outcome='Pass' — an inverted derived fact. mag_mpo/CLAUDE.md:87–101 meanwhile asserts 'NO roll call, NO per-member vote … even on divided votes' and "outcome='Fail' (3 motions) is the only dissent the record exposes" — a documented ceiling the source contradicts by naming 12 dissenters, the repo's own stated worst failure mode. Doc correction alone is S; extractor fix + re-federate is M.

### TODO.md:452 — (j2) died-for-lack-of-a-second motions carrying the SUBSTITUTE motion's roll call (weber ×4; also ogden ×2 + midvale ×1, unrecorded)
*real-open · relevance: medium · effort: M · section 43-560*

Confirmed by join of motion_std.outcome='died' against motion.outcome='Pass': weber_county 2018-07-03 m6, 2018-09-11 m6 and m7, 2018-12-18 m13 — all four carry a named roll call, and weber_county/legislative/minutes/2018/2018-09-11_commission.md:311,323 shows the merge exactly ('Motion died for lack of a second. Chair Harvey moved to adopt Ordinance 2018-14 …; Commissioner Ebert seconded' then the roll). The entry's claimed summit_county row is NOT the same defect — summit_county 2015-08-20 m5 has an empty outcome (an honest blank), so that half is not-an-issue. The entry also MISSES three city rows in the same class: ogden 2023-10-10 m7 and 2025-05-20 m6 (motion_text literally contains 'The motion died for lack of a second' with outcome='Pass') and midvale 2020-06-30 m3. Effect is a handful of ordinance/rezone motions whose votes are attributed to the wrong motion text; ogden ORD 2023-56 links to a different motion, so no ordinance quote is currently wrong.

### TODO.md:556 — Follow-up inside the [x] disposition item — legacy `recommendation` field contradicts disposition∘outcome (filed as 13; measured ~68)
*real-open · relevance: high · effort: M · section 43-560*

Confirmed and larger than filed. Composing disposition with carriage against the stored value on stage='pc_recommendation' motions (5,422 with a recommendation) returns ~68 contradictory rows spread over 25 entities — e.g. herriman ×5 and south_jordan ×3 stored 'Positive' where disposition='deny' AND outcome='Pass' (the matter was DENIED), st_george ×6 and orem ×3 stored 'Positive' on a failed approve motion, slc ×4 and provo ×3 stored 'Negative' on a carried approve motion. This is not cosmetic: v_pc_divergence (a flagship view named in root CLAUDE.md) reads pc_recommendation directly and returns 1,149 rows / 85 flagged diverged, so some divergences are inverted or missed. Fix as described in the entry — derive recommendation from _compose_dir(disposition, outcome) — then re-verify the '269 Positive / 45 Negative' and v_pc_divergence figures downstream. Note the item's checkbox is [x] while this follow-up is live.

### TODO.md:1048 — [DEBT] weber_county — 2019-07-30 Solar Overlay adopting motion + roll call never extracted (mid-roll amendment defeats extractor)
*real-open · relevance: medium · effort: S · section 995-1124*

Confirmed exactly as filed. gov.db: the 2019-07-30 weber_county meeting holds motions 1–14; #13 is 'Commissioner Froerer moved to adopt Ordinance 2019-14…' and there is NO motion for Ordinance 2019-13 (a full-corpus `motion_text LIKE '%olar%'` scan for weber_county returns only 2019-02-05 Ord 2019-2 and a 2019-09-17 appointment). The ordinance row exists and is honestly labelled: `SELECT ordinance_no, adoption_date, motion_id, motion_resolution FROM ordinance WHERE city='weber_county' AND ordinance_no LIKE '%2019-13%'` → 2019-13 | 2019-07-30 | NULL | 'unlinked'. Because the gap is labelled `unlinked` rather than mis-linked, no researcher gets a WRONG answer today — only a missing one; but the extractor bug class (roll interrupted by 'amended his motion') could silently drop other motions in weber, so the S-sized fix in /Users/tysonwelsh/civic-data/weber_county/db/extract_votes.py is worth doing soon after ship.

### TODO.md:1109 — Suspicious closure sub-claim inside the Riverton wave-2 note: the 5 auth-wall rows were NOT set to fetch_status=error:auth_wall
*partially-done · relevance: low · effort: S · section 995-1124*

The wave-2 note (TODO.md:1107-1111) states all 5 sibling attachments on riverton 2026-04-21 (att8–att12) were 'corrected to fetch_status=error:auth_wall, format=na', and /Users/tysonwelsh/civic-data/riverton_city_council/packets/AVAILABILITY.md:97 repeats it. Only HALF landed: parsing index.csv shows all 5 rows do carry format='na', but their fetch_status values are '' (att8, att9, att11, att12) and still 'needs_ocr' (att10, the CC staff report). `grep -c 'error:auth_wall' riverton_city_council/packets/index.csv` returns 0. So the escape vocabulary the doc advertises is absent from the data — a documentation/data mismatch in exactly the honest-labeling layer this repo sells. Impact is small (5 rows, one city, and gov.db's `document` view of them is honest via has_text=0), but it is cheap to fix and it is the kind of claim an auditing reader would spot-check.

### TODO.md:1250 — Phase 4 closure note quotes superseded federation counts (county motions 24,346 / votes 35,318)
*stale-already-done · relevance: low · effort: S · section 1125-1557*

gov.db today reports county motions 27,269 and the 2026-07-29 re-federation is recorded at TODO.md:1084-1087 as having moved county motions to 27,376 / votes 39,237 — so the Phase-4 [x] block's numbers are two generations stale AND neither figure matches the live db (27,269 vs the 27,376 quoted in both TODO.md:1086 and root CLAUDE.md), which means a later rebuild moved the count again unrecorded; the closure note should be stamped 'counts as of 2026-07-20' rather than read as current.

### TODO.md:1301 — Phase-4 follow-up (E) small — SLCo Housing Authority minutes_index 69 rows vs 68 files
*real-open · relevance: low · effort: S · section 1125-1557*

Confirmed exactly: salt_lake_county/agencies/housing_authority/minutes_index.csv parses to 69 rows while `find .../minutes -name '*.md'` returns 68 — one index row has no file behind it, a one-row phantom in the document catalog that should either get a minutes_status explaining the absence or be removed.

### TODO.md:1372 — Phase-5 follow-up — legislator party/district backfill
*real-open · relevance: high · effort: M · section 1125-1557*

gov.db's `person` table is (city, gov_level, state, person_id, full_name, name_key) — there is NO party or district column at all, and ut_state contributes 222 persons with none; 'how did Republicans vote on the ADU bill' is one of the most obvious questions this 27,887-vote layer invites and it currently cannot be answered inside the db at all.

### TODO.md:1426 — Phase 6 closure note quotes superseded federated state (county motions 24,346, regional 958)
*stale-already-done · relevance: low · effort: S · section 1125-1557*

Live gov.db gives motions 49,172 city / 27,269 county / 959 regional / 1,208 state — city and state match the note, regional is off by one and county by ~3,000; same remedy as the Phase-4 note (date-stamp the figures), and the same reason to trust only live SQL when writing publication docs.

### TODO.md:1430 — Phase-6 residual — cosmetic `cities.db` strings in script comments
*real-open · relevance: low · effort: S · section 1125-1557*

36 occurrences across 8 files (scripts/build_cities_db.py, build_search_layer.py, normalize_motions.py, db_build_lib.py, rebuild_derived.py, extract_packet_text.py, roster_lib.py, weeks_lib.py); most are harmless comments, but two are reader-facing and now false — build_cities_db.py:780 'Elections are not in cities.db' (election_race/election_result have existed since 2026-07-11) and build_search_layer.py:713's error string 'cities.db not found' when the constant at line 56 is gov.db.

### TODO.md:1432 — Phase-6 residual — v_pc_divergence / referral layer never extended to the county tier
*real-open · relevance: medium · effort: L · section 1125-1557*

`SELECT city, COUNT(*) FROM v_pc_divergence GROUP BY city` and the same over `referral` both return CITY slugs only — no county has a single referral row, so the documented flagship query 'did the PC recommend against something the Council passed' silently returns nothing for salt_lake_county/summit_county/utah_county even though those entities have both PC and legislative motions; needs either a county referral build or an explicit caveat/doc line saying the view is city-tier only.

### TODO.md:1793 — Ogden referral guard — STILL OPEN: enable the shared-lib guard for cities beyond ogden
*real-open · relevance: medium · effort: L · section 1558-1920*

Verified genuinely open and correctly described. scripts/referrals_lib.py carries the four opt-in params (member_names / template_stopwords / content_veto / name_anchor_min — declared at lines 29-45, IDF.__init__ line 123, main() lines 198-199, all defaulting to a faithful no-op), and `grep -ln content_veto */db/build_referrals.py` returns exactly ONE file: ogden_city_council/db/build_referrals.py. Ogden's proven yield was 13→6 links with all 7 dropped verified false positives, so the same surname/template FP class plausibly inflates other cities' referral tables (lehi 458, bluffdale 269, provo 165 rows in gov.db). Not a blocker because referral rows carry confidence and CLAUDE.md already instructs 'low = don't quote', but it degrades v_pc_divergence / v_referral_chain precision. Requires per-city evidence review — L.

### TODO.md:1932 — Convention note "promoted-doc weeks bundles show Meetings: 0" — 206 contradictory bundles, and bluffdale's 136 have a different, unrecorded cause
*partially-done · relevance: medium · effort: S · section 1921-2158*

TODO.md:1932-1933 records as an accepted "convention" that promoted-doc weeks bundles print "Meetings: 0" with votes present (midvale/magna/alta pattern). Scanned every */weeks/*/summary.md: 206 bundles say "Meetings: 0" while "Votes: N motions" with N>0 — bluffdale 136, herriman 18, vineyard 13, midvale 13, magna 10, south_jordan 7, riverton 5, alta 3, orem 1. The bluffdale majority is NOT the documented pmn pattern: e.g. /Users/tysonwelsh/civic-data/bluffdale_city_council/weeks/2020-01-15/summary.md says "Meetings: 0 / Votes: 12 motions" while its votes.csv `source` is an ordinary audited file `minutes/2020/2020-01-13/council_2020-01-15_706.md` listed in minutes_index.csv:3. Cause is /Users/tysonwelsh/civic-data/scripts/weeks_lib.py:91-93, which derives a meeting's date from `f.stem[:10]` — bluffdale is the only city whose minutes filenames are not date-prefixed (166/166 files named `council_YYYY-MM-DD_NNN.md`), so `iso()` fails and every bluffdale bundle reports zero meetings and links no minutes (`meeting_types = f.stem[11:]` has the same assumption). weeks/ is one of the four artifacts CLAUDE.md tells researchers to use, and a bundle that shows meetings=0 next to 12 motions reads as a data error; the fix is a filename-vs-index date lookup in one shared helper.

### TODO.md:2155 — Notes: emigration_canyon VERIFICATION.md carries pre-existing T3.1(k) staleness
*real-open · relevance: low · effort: S · section 1921-2158*

Read /Users/tysonwelsh/civic-data/emigration_canyon_city_council/VERIFICATION.md and cross-checked every claim. It is stale in three ways: (a) line 30 asserts 'db/civic.db PASS — 429 motions (Council 288 + PC 141) … reconciles exactly', but gov.db now has Council 297 / PC 141 for emigration_canyon (the LM-wave +1 council motion at TODO.md:1941 plus later recoveries), so the doc's headline reconciliation figure is wrong; (b) its closing paragraph still states the "2nd by:" seconder ceiling stands corpus-wide, which TODO.md:1941 says was fixed 2026-07-17 (124/141 filled); (c) line 219 reports a live `validate_city.py` FAIL for a missing `crosswalks/vote_values.csv` Recuse row — that row now exists (crosswalks/vote_values.csv:84, and gov.db `vote_values` returns the emigration_canyon/Recuse row). A per-city VERIFICATION doc that contradicts the shipped data is a trust problem for anyone auditing the repo, but it is one small city's doc, not a query surface — cheap doc refresh right after publish.

### TODO.md:2164 — SLC campaign_finance — portal-blocked honest gap (re-run harvest when dotnet.slcgov.com is back up)
*real-open · relevance: medium · effort: S · section 2159-2782*

Checked slc_city_council/campaign_finance/: index.csv is header-only (1 line), raw/ is empty, and `SELECT city FROM cf_cycle` in gov.db returns 29 cities with slc absent. Real-open; matters because Utah's largest city is silently missing from every cross-city money query and cities_db_SCHEMA.md (lines 30/121/124) never states which cities cf_* covers.

### TODO.md:2420 — Ogden CF (b) — 18 primary-candidate filings absent from election_results; 'a future election_results review lead'
*real-open · relevance: medium · effort: S · section 2159-2782*

gov.db election_race for ogden has ZERO primary rows (only 4 municipal general rows per cycle 2019–2025), while murray/holladay/cottonwood_heights/herriman/south_salt_lake/park_city all carry primaries. ogden_city_council/election_results/CLAUDE.md line ~115 says 'Primaries not output — per the task' and the 2021/2023 primary PDFs are already in raw/ — so the raw material is on disk and this is a cheap fix; left open it is a silent cross-city asymmetry no federated doc discloses.

### TODO.md:2540 — South Salt Lake (b) [med] — 2021 3-way mayoral primary absent from election_results; also the 'missing 2011/2019 SSL rows'
*partially-done · relevance: medium · effort: S · section 2159-2782*

The 2011/2019 half is DONE — gov.db election_race has south_salt_lake 2011 (4 general + 1 primary) and 2019 (4 general + 4 primary). The 2021 mayoral primary is STILL missing: SSL primary rows stop at 2019 while 2021 has only 4 general rows (Mayor: Wood def. Christensen). CF filings prove the primary happened, so a researcher asking 'did SSL hold a 2021 primary' gets a false negative.

### TODO.md:2620 — Draper (b) [med] — cf-vision-transcribe the CF layer (125 filings, 116 scanned)
*real-open · relevance: high · effort: M · section 2159-2782*

draper_city_council/campaign_finance/ contains ONLY AVAILABILITY.md, CLAUDE.md, index.csv and raw/ — no contributions.csv/expenditures.csv/filing_totals.csv — and draper is absent from gov.db cf_cycle (29 cities present). With SLC (line 2164) these are the only 2 of 31 cities missing from the CF layer, and cities_db_SCHEMA.md lines 30/121/124 never state the covered-city set, so a cross-city 'who funded whom' query silently under-counts Draper's 125 filings and 2011–2025 depth.

### TODO.md:2859 — REMAINING OWNER QUESTIONS (i) bluffdale Hall Dec-04 period, (ii) holladay Tracy index date/label swap
*real-open · relevance: medium · effort: S · section 2783-3495*

Verified BOTH still open: holladay_city_council/campaign_finance/index.csv rows 16-17 still read 2023-10-31 '7-day pre-general' and 2023-11-01 'period not stated' — the stamped-form dates (Nov-14 / Oct-24) were NOT applied; gov.db cf_cycle shows bluffdale NATALIE HALL 2025 spent=18471.66 basis='sum-interim', i.e. the Dec-04 Final was NOT folded in. A researcher reading holladay filing dates gets swapped labels; Hall's spent may be ~$4.2k low.

### TODO.md:2881 — CF follow-up (e) — murray 2021 Mayor+D4 primary discrepancy flags, fold into elections review
*unverified · relevance: medium · effort: S · section 2783-3495*

I did not open murray's 2021 primary rows; the entry says CF filings imply a primary the election layer may record differently. If real it means election_race/election_result disagree for a murray 2021 contest — the class of defect that the slc 2019/2021 fix (lead (m), line 3120) proved can reach the AUDITED races CSV. Cheap to settle; unresolved election facts are exactly what outside researchers will quote.

### TODO.md:3200 — LM wave (u) — other cities adopt the recovered 2021 tallies / re-point 7 city election pipelines at the county canonical
*partially-done · relevance: medium · effort: M · section 2783-3495*

The specific alta case is CLOSED: blank winner_votes in gov.db election_race now appear only for alta 2025 (2), magna 2023 (3), millcreek 2023 (2) — alta's suppressed 2021 blanks are filled. The general half (7 city election pipelines still not re-pointed at the audited county canonical) remains open, and the slc lead-(m) fix proved that divergence can reach the AUDITED per-city races CSV — election numbers are among the most quotable things a researcher will take from this repo.

### TODO.md:3612 — Midvale PC extractor: Erikson/Erickson name variant un-normalized
*real-open · relevance: medium · effort: S · section 3496-3786*

Confirmed still open: /Users/tysonwelsh/civic-data/midvale_city_council/planning_commission/all_votes.csv has 975 'Erickson' vs 18 'Erikson', and gov.db has TWO person rows for midvale — 'Erickson' (267 votes, 2020-05-13..2026-06-10) and 'Erikson' (13 votes, 2022-08-10..2022-09-28). v_member_record_all therefore splits one commissioner's record and undercounts by 13 votes for anyone querying 'Erickson' — a genuinely wrong answer to a common per-member question, though scoped to one member in one city.

### TODO.md:3641 — Bluffdale — referral layer spot-check + precision-tune (269 links, high vs peers)
*real-open · relevance: medium · effort: M · section 3496-3786*

gov.db referral for bluffdale = 269 rows split exactly 189 high / 69 medium / 11 low, matching the filed numbers — no tuning pass has run. Bluffdale is the #2 referral city behind lehi (458) despite being small, so v_pc_divergence / v_referral_chain results for bluffdale may over-report PC→Council linkage. Mitigated by the documented 'confidence: low = don't quote' rule, so misleading only to a user who ignores the confidence column. NOTE the entry's own warning: build_db.py DROPS the referral table — do not rebuild casually.

### TODO.md:3770 — [med] Draper election_results acquisition gap — 2025 CANCELED-uncontested 2-seat 4-year Council race (Res #25-49; Tasha Lowery + Mike Green)
*real-open · relevance: medium · effort: S · section 3496-3786*

Confirmed: /Users/tysonwelsh/civic-data/draper_city_council/election_results/draper_races.csv has only THREE 2025 rows (lines 22-24) — municipal general At-Large 2-YEAR TERM, Mayor, and the At-Large primary. No 4-year 2-seat contest exists, because SLCo's SOVC never printed one. Consequence: two sitting Draper councilmembers are invisible to election_race / v_election_city and to any roster↔election crosscheck, and a researcher asking 'who won Draper 2025' gets an incomplete answer with no gap marker. Small, bounded fix (2 certification rows + a note). This is the ONLY still-open item in the 2026-07-29-reworked votes-pipeline section, exactly as its own annotation states.


## Backlog is fine (no publication impact) (124)

### TODO.md:45 — [DEBT] NON-CITY-TIER AUDIT FIXES (parent entry, lines 45–546)
*partially-done · relevance: medium · effort: M · section 43-560*

Walked all 20 lettered/tiered sub-items across 502 lines: (a)(b)(c)(d)(e)(f)(g)(h)(h2)(h3)(h4)(i)(j)(l)(m), TIER-4 and the TIER-5 provenance half are all closed with dated notes, and I spot-verified several against gov.db (weber 4,404 motions / 12,585 votes post-OCR; utah_county 11,218 motions with named divided votes in every year 2019–2026; wfrc 0 files carrying U+202A-E marks and 0 result_raw beginning 'ith '; cache Chris Sands now on 8 of 9 rolls at 2024-11-07; fts_minutes 13,886 rows / 40 entities matching the docs; v_coverage 82 rows). Genuinely open remainders are only: (e2) 4 wfrc motions, TIER-3 washington + mag garbling, (j2) weber died-motion merges, plus two NEW stale-artifact defects the entry itself created (see rows at lines 410 and 491). ~90% of the entry's bulk is historical record that belongs in TODO_ARCHIVE.md — as written it reads as one huge open DEBT item and makes the backlog look far larger than it is.

### TODO.md:215 — (e2) wfrc_mpo — 4 appositive motions with no mover, never extracted
*real-open · relevance: low · effort: S · section 43-560*

Verified at source and in gov.db: wfrc_mpo/legislative/minutes/2017/2017-03-23_council.md:287 ('Mayor Tom Dolan, Chair of the Budget Committee, made a motion to open a public hearing') and 2023/2023-08-24_council.md:170,176 (Caldwell / Silvestrini station-area-plan motions) have no corresponding row — the db holds 7 motions for 2017-03-23 and 5 for 2023-08-24, none matching those texts; `SELECT count(*) FROM motion WHERE city='wfrc_mpo' AND mover_person_id IS NULL` = 0, i.e. the motions are absent rather than mover-less. 4 missing motions out of 324 in a vote-less DATA-FORWARD entity whose analytic surface is regional_project, so no researcher conclusion turns on them; the entry itself warns the regex is collateral-damage-prone.

### TODO.md:405 — TIER 3 residual — washington_county OCR garbling (shredded ALL-CAPS headings + ligature loss)
*real-open · relevance: low · effort: S · section 43-560*

Confirmed by grep: 3 legislative minutes files match the spaced-caps pattern (e.g. washington_county/legislative/minutes/2022/2022-09-06_board_of_commissioners.md) and ≥6 files show fi/fl ligature loss ('ofce', 'conrm') including land_use/minutes/2023/2023-02-14_planning_commission.md. washington_county is db-less by design, so the only consumer is fts_minutes keyword search — a searcher for 'office' misses those tokens. Real but marginal; the entity's 82%-OCR ceiling is already caveat-carried.

### TODO.md:998 — [OPTION] STATE TIER — reevaluate how ut_state is integrated, on its own terms (owner ruling 2026-07-29)
*real-open · relevance: medium · effort: XL · section 995-1124*

All three structural claims verified read-only against /Users/tysonwelsh/civic-data/gov.db: (1) no table named '*bill*' exists (sqlite_master), and ut_state rows appear ONLY in generic tables (motion 1208, vote 27887, person 222, meeting 541, body 23, application 264, projection 140, document 527) — zero purpose-built tables, vs wfrc_mpo's four; (2) `SELECT count(*) FROM application WHERE city='ut_state'` = 264, i.e. bills really do sit in the municipal-development-application slot, while /Users/tysonwelsh/civic-data/ut_state/legislation/bills.csv exists on disk (265 lines = 264 bills + header) unmodelled; (3) `SELECT count(*) FROM motion_std WHERE city='ut_state'` = 0. MITIGATION ALREADY SHIPPED: the caveat table carries 3 ut_state rows (disjoint-persons, vote-ceiling, motion-std-deferred), and the motion-std-deferred caveat text spells out the bill-as-application problem verbatim and points at this TODO item — so a researcher who reads caveats is warned. Residual publication risk is a naive cross-tier `SELECT count(*) FROM application` that silently counts 264 bills as development applications; that is niche, not a common query. This is a design program (bill/bill_stage/bill_sponsor spine + statute spine), multi-session at minimum, and explicitly an [OPTION] — do not let it gate shipping.

### TODO.md:1071 — [DEBT] (a) emigration_canyon parse_present() credits ABSENT members as present
*real-open · relevance: low · effort: S · section 995-1124*

Reproduced at source. /Users/tysonwelsh/civic-data/emigration_canyon_city_council/meeting_minutes/minutes/2024/2024-07-30/2024-07-30_city-council-meeting-1239935.md prints 'Council Member(s) Absent:' then 'Catherine Harris, Council Member', yet /Users/tysonwelsh/civic-data/emigration_canyon_city_council/meeting_minutes/votes/2024/2024-07-30/2024-07-30_city-council-meeting-1239935.json lists Catherine Harris in `present` (and every motion that day carries a 4-0 tally with 'Council Member Harris was absent from the vote' in the text). Cause is visible in extract_votes.py:203 `parse_present()` — it scans a fixed 500-char region after the PRESENT header for roster surnames, so the following Absent block is swallowed. Publication relevance is LOW because gov.db has NO attendance/roster-of-presence table (table list confirmed: body/person/meeting/…/term/district_version/district_precinct — nothing attendance-shaped), so the error is confined to one entity's on-disk meeting_minutes/roster.csv `n_meetings` column plus the per-meeting JSON; votes and tenure bounds are untouched, as the entry states.

### TODO.md:1079 — [DEBT] (b) scripts/db_build_lib.py kind_of() mints kind='committee' only on 'board', so alta BudgetCommittee lands as 'council'
*real-open · relevance: low · effort: S · section 995-1124*

Confirmed verbatim at /Users/tysonwelsh/civic-data/scripts/db_build_lib.py:38 — `if "board" in n: return "committee"` with no 'committee' keyword anywhere in kind_of(), so any body named '…Committee' falls through to the `return "council"` default. As the entry says, `body.name` remains correct and authoritative, so only the coarse `kind`/`stage` classifier is imprecise; a researcher filtering on body.name gets the right answer. Genuinely cosmetic, and it is a SHARED script (all 31 city builds import it), so the fix costs a repo-wide rebuild — poor value before shipping.

### TODO.md:1093 — [DEBT] Riverton Timberline DA staff report re-acquisition (auth-walled Granicus object)
*real-open · relevance: low · effort: M · section 995-1124*

Confirmed open and correctly characterised. /Users/tysonwelsh/civic-data/riverton_city_council/packets/index.csv:2870 holds the 2026-04-21 '26-06 Timberline Development Agreement CC Staff Report' row at 4,629 bytes with extraction_method 'none (Granicus auth-wall HTML capture; login-gated PDF - see AVAILABILITY.md)'. In gov.db the row surfaces in `document` with has_text=0, which is honest — no researcher is misled, they simply cannot read one staff report (and the PC staff report for the SAME project IS present with 45,741 chars of text, so the substantive record is not lost). Both public probes are documented dead and GRAMA is the only channel, so effort is unbounded-by-others; classic backlog. Do NOT let one document gate publication.

### TODO.md:1114 — [OPTION] Primary-document WATCH LIST — assess cost/benefit before admitting any class
*not-an-issue · relevance: none · effort: S · section 995-1124*

Verified the referenced register exists and is populated: /Users/tysonwelsh/civic-data/PRIMARY_DOCS_PILOT_SPEC.md:204 '## Appendix A — Watch list: deferred document classes (assess cost/benefit before admitting)', with the spec's line 5 pointing to it. This is not a defect and not deferred work — it is a standing scope-control register whose whole purpose is to STOP classes being admitted without a written cost/benefit, i.e. it is an anti-refinement-creep device and directly aligned with the owner's ship-now posture. Nothing about it makes gov.db or the top-level docs wrong. Keep it, but it should arguably be reclassified out of TODO into a 'registers / not-work' section so it stops reading as an open task; its trigger ('revisit after the Sandy pilot ships') is the only thing to re-check later.

### TODO.md:1282 — Phase-4 follow-up (A) — per-city election re-point package to the 6 new county canonicals (park_city/st_george/lehi/provo/orem/vineyard/logan/ogden)
*real-open · relevance: low · effort: L · section 1125-1557*

Listed all 8 cities' election_results/ dirs — every one still carries its own raw/ plus clean_elections.py/build_*_elections.py, so none has been re-pointed; this is a dedup/lineage consolidation, and the audited <city>_races.csv remain authoritative either way, so nothing an outside researcher reads is wrong today (the one thing worth doing first is the banked park_city 49/50-row mismatch, the same shape as the taylorsville real finding).

### TODO.md:1289 — Phase-4 follow-up (B) — utah_county PC minutes backfill, 46 meetings 2020–2024 (media host NXDOMAIN)
*real-open · relevance: medium · effort: M · section 1125-1557*

utah_county/land_use/minutes_index.csv has exactly 46 rows with minutes_status='catalogued_media_offline' (plus 72 no_minutes / 11 Approved / 10 Cancelled / 6 Scheduled) and only 11 rows carry md_path; on disk utah_county/land_use/minutes/ holds only 2025 (7) and 2026 (4) files — so the gap is real, exactly as stated, and honestly ledgered per-row, which keeps it from being misleading.

### TODO.md:1292 — Phase-4 follow-up (C) — OCR-gated legislative depth backfills (cache 2015–2020 + 1995–2014, weber 2000–2014, summit pre-2023, washington pre-2019)
*partially-done · relevance: low · effort: L · section 1125-1557*

cache_county/legislative/minutes/ and weber_county/legislative/minutes/ both now span 2015–2026 (the cache 2015–2020 scanned backfill landed with the 2026-07-25/26 Tier-1 fixes noted at TODO.md:1084), but summit_county/legislative/minutes/ starts at 2023 and washington_county/legislative/minutes/ starts at 2019 — so the entry's cache-2015–2020 clause is stale while the deep-archive and summit/washington clauses are genuinely open.

### TODO.md:1296 — Phase-4 follow-up (D) — elections residue (cache 2024 image-only canvass + 2006–2016 GEMS, weber GEMS precinct grids, washington 2019-08 GRAMA + 2018-06 scan, summit 2022/2024 primaries)
*unverified · relevance: medium · effort: L · section 1125-1557*

Did not open each county's raw election archive; election_result in gov.db is 5,482 rows across all 7 counties and each county's elections/ carries CLAUDE.md + VERIFICATION.md, so the covered eras are documented — these are named extensions to an already-marquee layer rather than corrections, and they matter only for pre-2019/off-year queries.

### TODO.md:1302 — Phase-4 follow-up (E) small — summit PMN-1503 gap recovery + 14 image-only PC minutes OCR + pre-2024 DocumentCenter staff-report pass
*real-open · relevance: low · effort: M · section 1125-1557*

summit_county/land_use/minutes_index.csv has 393 rows of which exactly 14 are minutes_status='minutes_exist_text_unrecovered' — the image-only set is real and precisely ledgered (so FTS honestly under-covers those 14 dates rather than misreporting); the PMN-1503 and staff-report clauses were not separately verified.

### TODO.md:1304 — Phase-4 follow-up (E) small — cache PC 14 minutes-less dates via PMN 1479
*real-open · relevance: low · effort: S · section 1125-1557*

cache_county/land_use/minutes_index.csv has 141 rows with exactly 14 marked 'NoMinutesPosted' (plus 4 PendingApproval) — the count in the TODO matches the file, and the gap is recorded per-date, so it reads as an honest gap not a silent hole.

### TODO.md:1304 — Phase-4 follow-up (E) small — weber WWPC-2020 GRAMA request
*unverified · relevance: low · effort: S · section 1125-1557*

Not independently checked; weber_county has no development/ or packets/ dir and its planning layer is documented as FTS-only, so a single 2020 Western Weber PC records request is a marginal depth addition, and it is gated on an external agency response anyway.

### TODO.md:1306 — Phase-4 follow-up (E) small — weber planning FTS→votes promotion (conditional on Ogden Valley priority)
*real-open · relevance: none · effort: M · section 1125-1557*

weber_county/ has no land_use vote layer (land_use is documented FTS-only, consistent with the entry) and the item is explicitly self-gated 'only if Ogden Valley/W-Weber becomes a priority' — it is a conditional scope option, not a defect.

### TODO.md:1307 — Phase-4 follow-up (E) small — summit HA/RDA build-later
*real-open · relevance: none · effort: M · section 1125-1557*

summit_county/agencies/ exists but the entry itself declares the HA nascent (minutes accumulating since 2025-08) and the RDA thin — deliberate deferral recorded at build time, so nothing an outside researcher queries is wrong.

### TODO.md:1308 — Phase-4 follow-up (F) — fold the PMN JSON-POST/X-CSRF search channel into pmn_crosscheck/refresh tooling
*partially-done · relevance: low · effort: S · section 1125-1557*

grep for 'searchresult|CSRF|POST' finds NOTHING in scripts/pmn_crosscheck.py or scripts/pmn_crosscheck_HARDENING.md, so the tooling fold-in is genuinely open — but the knowledge itself is already captured in ~/.claude/skills/build-county-data-repo/SKILL.md:143-144, so the only loss is convenience on the next refresh.

### TODO.md:1371 — Phase-5 follow-up — ut_state 2025/2026 committee-vote (mtgvotes) linkage residual
*real-open · relevance: medium · effort: M · section 1125-1557*

CONFIRMED by file: ut_state/legislation/rollcalls.csv carries 1,137 rows with vote_type floor 798 / committee 339 for sessions 2015GS–2024GS, while rollcalls_recovered.csv's 71 rows (2025GS 38 + 2026GS 33) are 100% vote_type='floor' — so committee action on the two most recent sessions' bills is absent, and a 'did this bill die in committee in 2025' question gets an incomplete answer.

### TODO.md:1372 — Phase-5 follow-up — ut_state special-session sweep
*real-open · relevance: medium · effort: M · section 1125-1557*

Every session value in both rollcall files is a General Session ('2015GS'…'2026GS'); no S1/S2/special-session codes appear anywhere, so any land-use bill moved in a special session is simply not in the 264-bill subset — the subset is documented as a curated land-use slice, which limits the harm, but the GS-only boundary should be stated explicitly wherever the subset is described.

### TODO.md:1374 — Phase-5 follow-up — advisory opinions #102/#206 (Wayback-dead) + #142/#145 image-only
*real-open · relevance: low · effort: S · section 1125-1557*

ut_state/advisory_opinions/index.csv has 309 rows of which exactly 307 carry both path and text_path — the 2 text-less rows match the claimed #102/#206, and the catalogue itself makes the gap visible, so a researcher sees 'no text' rather than a wrong answer.

### TODO.md:1375 — Phase-5 follow-up — late-2025 year-sequential advisory-opinion series
*unverified · relevance: low · effort: S · section 1125-1557*

Could not cheaply confirm whether OPRO switched to a year-sequential numbering series in late 2025 without hitting the (Cloudflare-walled) source; the in-repo index is complete against its own 309-row catalogue, so the risk is a tail of newer opinions rather than a defect in what exists.

### TODO.md:1375 — Phase-5 follow-up — WFRC historical seat-tenure roster
*real-open · relevance: low · effort: M · section 1125-1557*

wfrc_mpo/roster/ contains only council_seats.csv with 28 rows keyed by an `as_of` column — a current snapshot, no start/end tenure intervals, so the 'who sat on WFRC in 2019' question is unanswerable; the raw material (every meeting's member table) is already in the repo, so this is derivable work.

### TODO.md:1376 — Phase-5 follow-up — MAG ~15 surname-only movers 2014–19
*unverified · relevance: low · effort: S · section 1125-1557*

Not separately counted; mag_mpo's vote table is empty by source (tally-only) so these surnames only affect mover/seconder attribution on 635 motions, and the repo's standing rule against surname-only resolution means leaving them unresolved is the honest state.

### TODO.md:1377 — Phase-5 follow-up — RTP2027 refresh seam (both MPOs; drafts catalogued, never blended)
*not-an-issue · relevance: none · effort: S · section 1125-1557*

This is a monitoring rule (append-never-blend across vintages) already encoded in the refresh-city/audit skills per the Phase-6 note at TODO.md:1415-1417, and the project_vintage/project_history design plus 4 caveat rows already enforce vintage separation — nothing is broken today.

### TODO.md:1378 — Phase-5 follow-up — wfrc 2016 .WMA audio unswept
*unverified · relevance: low · effort: M · section 1125-1557*

Not checked at the source host; WFRC Council minutes 2016+ are already born-digital and federated (324 motions), so audio would only add colour to a year already covered in text — low marginal value for transcription cost.

### TODO.md:1431 — Phase-6 residual — `cities_db_SCHEMA.md` keeps its pre-rename filename
*real-open · relevance: low · effort: S · section 1125-1557*

The file exists at /Users/tysonwelsh/civic-data/cities_db_SCHEMA.md (29 KB, current) and root CLAUDE.md points readers to it by name, so nothing breaks — but a newcomer to a repo whose database is gov.db will pause at a schema doc named for the legacy symlink; a rename plus reference sweep is optional polish.

### TODO.md:1434 — WFRC-NATIVE HOLISTIC PACKAGE — Phases 2–5 (plans capture + TIP funding parse, grant/cert/position tables, packets, MAG parity)
*real-open · relevance: none · effort: XL · section 1125-1557*

Phase 1 is verifiably built (wfrc_mpo/projects/derived/{project_vintage,project_history}.csv on disk; gov.db project_vintage=3,453 / project_history=1,884 / caveat=63; udot+uta registered), and Phases 2–5 are verifiably NOT (no project_funding, project_obligation, regional_grant, sap_certification or legislative_position tables exist in gov.db; wfrc_mpo/plans/index.csv is still the 28-doc Phase-0 corpus) — but WFRC_NATIVE_SPEC.md §5 frames these as pure capability expansion on an entity that already works, and the spec explicitly says implementation awaits owner go per phase, so this is the single largest 'refinement creep' magnet in the whole section and should be quarantined behind the ship.

### TODO.md:1492 — Phases 4–6 residual (1) — the County content menu is STILL OPEN (no county got the enrichment modules)
*real-open · relevance: low · effort: XL · section 1125-1557*

Confirmed by directory listing: no county has an rda/, interlocal/, cip/, permits/, campaign_finance/ or roster/ dir, and gov.db has 0 county rows in cf_contribution and 0 county rows in `term` — the residual is real, but it is scope expansion on entities that already ship a documented tier (LIGHT/MID/FULL), and every county's CLAUDE.md states its tier, so no answer is wrong today.

### TODO.md:1530 — County menu — RDA/CRA project-area plans + tax-increment financials
*real-open · relevance: none · effort: L · section 1125-1557*

No county directory contains an rda/ or tax-increment module (salt_lake_county/agencies/ holds only housing_authority plus a combined minutes set); this is a net-new dataset class, valuable but purely additive.

### TODO.md:1532 — County menu — interlocal & development agreements
*real-open · relevance: none · effort: L · section 1125-1557*

No county has an interlocal/agreements module; the only interlocal artifacts found anywhere are incidental ordinance rows in city sources (e.g. logan_city_council/sources.csv:1652) — genuinely unbuilt, and the entry's own pitch ('rarely assembled anywhere') marks it as a differentiator to build AFTER shipping.

### TODO.md:1535 — County menu — Legislative matter catalog (Legistar matters, Sandy-style)
*real-open · relevance: none · effort: M · section 1125-1557*

gov.db has no county matter table and the legistar_* extension tables are documented as living only in sandy's own db/sandy.db; salt_lake_county is the only Legistar county, so this would benefit exactly one entity.

### TODO.md:1537 — County menu — county campaign finance
*real-open · relevance: none · effort: L · section 1125-1557*

`SELECT city, COUNT(*) FROM cf_contribution GROUP BY city` returns 29 CITY slugs and zero counties — the layer is city-only, which the money-vs-votes documentation already implies, so extending it is expansion not repair.

### TODO.md:1543 — County menu — CIP / impact-fee facilities plans
*real-open · relevance: none · effort: L · section 1125-1557*

No cip/ or impact-fee module in any of the 8 county directories; unbuilt as stated, and it is an infrastructure-capacity dataset with no bearing on the correctness of anything currently published.

### TODO.md:1545 — County menu — building permits / housing starts
*real-open · relevance: none · effort: XL · section 1125-1557*

Unbuilt (no permits module anywhere) and the entry itself flags 'feasibility TBD — needs a county data portal'; it is a research question before it is a task, so it should be marked as a candidate rather than a queued item.

### TODO.md:1547 — County menu — cross-tier analytical views (county land-use actions ↔ member-city actions; RDA areas overlapping cities)
*real-open · relevance: medium · effort: L · section 1125-1557*

gov.db's view list is v_contested_all, v_council_current, v_coverage, v_election_city, v_landuse_outcomes, v_member_record_all, v_pc_divergence, v_term_provenance — none joins across gov_level, so the 4-tier entity model's headline promise ('research municipal government in ways not possible elsewhere') has no shipped cross-tier query surface; the raw joins are all available via entity_relationship, so this is arguably the single highest-leverage item in the menu for the publication pitch.

### TODO.md:1549 — County menu — County Council roster (roster layer generalized to counties)
*real-open · relevance: medium · effort: L · section 1125-1557*

`SELECT city, COUNT(*) FROM term GROUP BY city` returns 31 city slugs and zero counties, so v_council_current and the point-in-time roster pattern silently return nothing for any county; root CLAUDE.md does scope the roster layer to city entities, so the docs are honest, but a researcher who has learned the roster idiom on cities will hit an empty result on counties without an in-db signal.

### TODO.md:1569 — Wayback Machine archiving pass (submit every sources.csv URL to web.archive.org)
*real-open · relevance: low · effort: L · section 1558-1920*

Verified never run: `head -1 lehi_city_council/sources.csv` and `slc_city_council/sources.csv` show the schema is dataset,record_key,title,date,local_path,source_url,source_host,retrieved_date,verified_date,extraction_method,processing_ref — no snapshot/wayback column anywhere. The entry's scale figure is badly stale: it says '~6,700' URLs but the repo now holds 52,081 sources.csv rows / 46,522 distinct http URLs (7x). Owner-gated by design (NEXT_SESSION_PLAN.md:170 also lists it); citation durability is a trust nicety, not a correctness defect — no query returns a wrong answer because it is open. Update the URL count before scoping.

### TODO.md:1577 — Lehi council minutes publishing lapse (19 meetings after 2026-01-27 with no minutes)
*real-open · relevance: low · effort: S · section 1558-1920*

Confirmed still true on disk: `ls lehi_city_council/meeting_minutes/minutes/2026/` returns only 2026-01-05, 2026-01-12, 2026-01-26 — nothing after 2026-01-27. Already disclosed to readers at lehi_city_council/CLAUDE.md:189 ('19 meetings unposted on the portal — the staleness is city-side'). City-side publication gap, honestly documented; pure monitoring, no repo defect.

### TODO.md:1589 — St George 2025-10-09 work-meeting minutes (city published the wrong PDF)
*real-open · relevance: low · effort: S · section 1558-1920*

Verified logged with full forensic detail at st_george_city_council/meeting_minutes/minutes_unrecovered.csv line 2 (md5 96ec82b8… identical to the 2025.10.16 regular minutes on BOTH Revize and PMN 1347731, re-checked 2026-07-02; the wrong doc and its 70 misdated vote rows were removed rather than kept). The gap is recorded exactly as the cardinal 'honest gaps are data' rule requires — a researcher sees a documented hole, not a wrong answer. Watch-only until the city republishes.

### TODO.md:1594 — Orem PC 2025-10-15 minutes (CivicClerk serves the 11-05 file under both events)
*real-open · relevance: low · effort: S · section 1558-1920*

Verified logged at orem_city_council/planning_commission/minutes_unrecovered.csv line 12, with md5 382a9836e7015764fd6f3cb3ee35bf3b proving the duplicate and PMN notice 1027529 confirming only agenda/packet/resolutions exist; the meeting is proven held because the 11-05 minutes approve 'Minutes for the 10-15-2025 Planning Commission Meeting'. Same class as the St George item — honest, documented, watch-only.

### TODO.md:1714 — [roster] Historical council-district boundary acquisition (redistricting geometry gaps) — '5 of 9 DONE'
*partially-done · relevance: medium · effort: L · section 1558-1920*

Entry text is stale: it says 5 of 9 done with west_valley/slc/provo/ogden remaining. Disk shows SEVEN geo/council_districts_pre2022.geojson files — the named 5 (millcreek, sandy, south_jordan, taylorsville, west_jordan) PLUS slc and west_valley, both reconstructed 2026-07-19 per their roster/district_versions.csv notes. Those two notes also carry an important self-correction the TODO line does not reflect: a fragmentation control proved county-wide precinct renumbering, so ALL their prior-plan geometry was DOWNGRADED medium→low (slc D7 is a ~6-precinct fragment). Genuinely remaining: provo and ogden, whose geo/ dirs contain no pre2022 file and which need an external Utah/Weber County historical precinct fetch. Affects only pre-2022 address→district lookups in 2 cities, and existing reconstructions are honestly confidence-labelled — medium, not a blocker. Update the '5 of 9' header to 7 of 9.

### TODO.md:1801 — Ogden referrals follow-up (b): wider FP class — two different named CRAs sharing the generic 'Community Reinvestment Project Area' template
*unverified · relevance: medium · effort: M · section 1558-1920*

Could not cheaply confirm the manifestation count: the class is described qualitatively (needs project-noun-aware matching) with no named example rows, and ogden's own table is down to 6 links so any residue is in other cities' 1,600+ federated referral rows. Same risk profile as the guard-rollout item above (referral precision, confidence-labelled, not a wrong-answer blocker) and arguably should be MERGED into it rather than tracked as a separate lettered follow-up.

### TODO.md:1849 — [OPTION] Comments coverage — spoken-comment transcript layer for no-published-comment cities
*real-open · relevance: none · effort: XL · section 1558-1920*

Verified the premise arithmetic, with one drift: counting rows in every */public_comments/all_comments_clean.csv gives 23 of 31 cities at zero, not the entry's '24' — millcreek left the zero set when its in-packets harvest landed (9 letters), which the entry's own exclusion note anticipates. Every zero is honest-empty/submit-only and is documented as such, so no researcher is misled today. This is pure scope EXPANSION (a new Whisper/ASR-derived corpus across 23 cities, explicitly owner-gated for the audio-only tier) — the single largest unbuilt capability in this range, and correctly parked.

### TODO.md:1907 — Taylorsville geo: precinct-derived districts (no official council-district GIS layer exists)
*real-open · relevance: low · effort: S · section 1558-1920*

Real but externally blocked and fully disclosed: taylorsville_city_council/geo/CLAUDE.md line 6 has the heading 'No official district layer — polygons are PRECINCT-DERIVED', lines 19-20 say 'These follow precinct lines, which approximate but do not exactly equal the legal district boundaries. Treat near-boundary results as approximate', and line 123 repeats it as a caveat. The action ('source and swap in an official layer IF one is ever published') is contingent on a city publication that does not exist — a watch item mislabeled as DEBT.

### TODO.md:1911 — Taylorsville: 2 pending 2026 council meetings (2026-06-17 minutes not yet posted; 2026-07-01 cancelled)
*real-open · relevance: low · effort: S · section 1558-1920*

Confirmed on disk: taylorsville_city_council/meeting_minutes/minutes/2026/ ends at 2026-06-01, and 2026-06-17 is ledgered at taylorsville_city_council/meeting_minutes/minutes_unrecovered.csv line 2 ('Meeting held (agenda posted) but minutes not yet approved/posted to portal or PMN as of retrieval; only the agenda (docId 12079) was available'). One missing recent meeting, honestly recorded — this is ordinary refresh-cycle work, not a defect, and will be swept up by the next /refresh-city run rather than needing its own TODO line.

### TODO.md:1982 — Deferred rider inside the closed "recommend→Ceremonial" fix: 62 PC land-use recommendations still land in Other/low
*real-open · relevance: low · effort: M · section 1921-2158*

The [x] entry at TODO.md:1961-1986 explicitly parks a follow-up at lines 1982-1985 ("enhance land-use rules to catch plural 'Text Amendments'/'Chapter 17.x' … deferred because it would ripple to non-Ceremonial rows") that exists nowhere else in TODO.md. Verified the current state in gov.db: `SELECT classify_method, count(*) FROM motion_std WHERE classify_method LIKE '%rec-not-cere%'` returns exactly 62 rows, i.e. the shipped fix landed and those 62 PC recommendations are honestly `Other`/low today (out of 11,413 Other rows city-wide). Under-classification into an honest `Other` is a disclosed ceiling, not a wrong answer, and touching the land-use rules would ripple across the 31-city byte-stability gate — genuine backlog.

### TODO.md:1987 — [low] herriman Appeal Authority body modeling — 2 quasi-judicial hearing docs, no body in the model
*real-open · relevance: low · effort: S · section 1921-2158*

Both named docs exist: /Users/tysonwelsh/civic-data/herriman_city_council/pmn_backfill/raw/pmn_appeals_2025-02-20_1238575.pdf and pmn_appeals_2026-06-09_1451173.pdf (+ .md text sidecars), catalogued in that folder's index.csv with body key `AppealAuthority`, and pmn_bodies.csv:155 already flags PMN body 1171 as an "unmodeled quasi-judicial body (known repo-wide flag)". gov.db confirms no such body: herriman's bodies are CDRA (64 motions), Council (1214), HCFSA (31), HCSEA (39), PlanningCommission (926) — no appeals body. The gap IS honestly disclosed to readers at herriman_city_council/CLAUDE.md:209 ("AppealAuthority hearings (no appeals body in the city model — catalogued only)"), so no researcher is misled; the only downside is that the 2 docs are also absent from fts_minutes (0 rows for herriman with 'appeals' in path — the same doc_type exclusion as the line-1928 finding). This is one instance of a repo-wide class also queued at TODO.md:2407 (Orem BoA, owner-gated) and TODO.md:3320, so it should be worked as that class, not per city.

### TODO.md:2147 — Watches — 4 external portal/monitoring re-checks (magna CRA draft, SSL RDA, midvale RDA, SSL PC dup swap)
*real-open · relevance: none · effort: S · section 1921-2158*

Checked each on disk; all four are already honestly ledgered, so nothing is misrepresented to a reader. (1) magna 2025-11-18 CRA: the DRAFT is retained un-promoted at magna_city_council/pmn_backfill/index.csv:19 (raw/2025-11-18__cra-regular__1362717.pdf, title '…Minutes - DRAFT'), and the same date's two council meetings ARE in minutes_index.csv:160-161. (2) SSL 2025-02-12 RDA: recorded as an honest gap at south_salt_lake_city_council/meeting_minutes/minutes_unrecovered.csv:173 ('1 agenda-only cand'); the council meeting that night is captured (motions_std.csv:421-423). (3) midvale 2023-01-17 RDA: minutes_unrecovered.csv:2 carries a full explanation (the PMN doc labeled 'RDA Minutes 1-17-2023' is actually the 2022-12-06 minutes, promoted under their true date). (4) SSL 2023-09-21_pc: both copies present (planning_commission/minutes/2023/2023-09-18/2023-09-21_pc_PC.md audited; the AgendaCenter dup retained), and the item itself calls the swap 'optional' — one ADJOURN motion. These are outside-the-repo monitoring items with no defect behind them; keep as a watch list, do not gate publication on them.

### TODO.md:2150 — Watch sub-item: whether a 2024-08-06 midvale council meeting occurred at all
*unverified · relevance: low · effort: S · section 1921-2158*

This is the only Watches sub-item that is a factual question rather than a portal re-check. midvale_city_council/meeting_minutes/minutes_index.csv jumps 2024-07-16 (line 106) → 2024-08-13 (107) → 2024-08-20 (108), and minutes_unrecovered.csv has only 2 rows for all of 2024, none for 2024-08-06 — so the repo neither claims the meeting exists nor records it as a gap. A researcher is not misled (no phantom row), but the coverage ledger is silent where it should say either 'cancelled/summer recess' or 'minutes unrecovered'. Cheap to settle from the city agenda archive; low value.

### TODO.md:2153 — Notes: ~300 new murray PC motions postdate the motion-classification ground-truth audit (dispositions computed, unaudited)
*real-open · relevance: low · effort: S · section 1921-2158*

The claim's premise holds: the ground-truth audit is dated 2026-07-12 (_audits/2026-07-12-motion-classification/report.md) while murray's PC minutes recovery landed 2026-07-16, so the newer motions were never sampled. Sized it in gov.db: murray PlanningCommission has 678 motions (2020:141, 2021:127, 2022:110, 2023:88, 2024:108, 2025:78, 2026:26), of which 658 carry a `high` disposition_confidence (approve 480, procedural 163, continue 5, deny 5, table 5) and only 20 are low/NULL. So the exposure is a rule-based, high-confidence block in ONE city's PC — approve/deny rates are an advertised query surface (CLAUDE.md's disposition section), but the risk of a materially wrong aggregate is small and the honest-NULL convention still holds. Note it is recorded only as prose inside an un-checkboxed 'Notes:' bullet, so it can never be checked off.

### TODO.md:2233 — Park City (a) — 194 CivicClerk videos with ZERO captions; Whisper transcript layer is the only path to text
*real-open · relevance: low · effort: L · section 2159-2782*

park_city_city_council/transcripts/index.csv has 194 data rows, every one caption_type=none / extraction_method='ASR via Whisper deferred', and transcripts/text/ is empty. Genuinely open but it is pure scope expansion — no existing query returns a wrong answer because of it.

### TODO.md:2288 — Nephi (d) — full PMN body-1788 'Notice of Ordinance' harvest deferred (JS/opaque search)
*real-open · relevance: low · effort: M · section 2159-2782*

nephi_city_council/pmn_backfill/ contains council.json + cra.json but no body-1788 output. Real-open, but it is an ordinance-corroboration enrichment; nothing currently in the db is wrong without it.

### TODO.md:2322 — Vineyard (c) — 2023 campaign-finance cycle unrecoverable (CMS purge); re-fetch if the city re-posts
*real-open · relevance: low · effort: S · section 2159-2782*

Entry documents an external purge with Wayback returning only 404s; vineyard cf_cycle has 32 rows (other cycles built). This is a monitoring watch, not actionable work.

### TODO.md:2325 — Logan (a) — 2023 campaign-finance cycle (21 filings) provably unrecoverable online
*real-open · relevance: low · effort: S · section 2159-2782*

Entry documents Wayback 302→CDN 404s; logan cf_cycle has 18 rows for other cycles. Watch-only item.

### TODO.md:2351 — Logan — Ord 26-12 (Data-Center Moratorium) adopting meeting postdates the minutes ceiling; 'will be captured on the next fetch_new.py refresh'
*real-open · relevance: low · effort: S · section 2159-2782*

logan_city_council/meeting_minutes/minutes/2026/ still ends at 2026-06-01, so the post-2026-06 adopting meeting is still not in the repo. Correctly diagnosed as an honest ceiling; it self-resolves at the October quarterly refresh.

### TODO.md:2383 — Orem (a) — Drive-archive packet backfill for pre-CivicClerk 2020–2021H1 agenda packets (needs Drive API pass)
*real-open · relevance: low · effort: M · section 2159-2782*

orem_city_council/packets/index.csv earliest row is 2021-07-13 and the year histogram starts at 2021 (35 rows) — the 2020–2021H1 window is genuinely absent. Packets are a supplementary layer; no vote/motion answer changes.

### TODO.md:2406 — Orem (b)(ii) — 3 Board of Adjustment minutes STILL DEFERRED, OWNER-GATED (body not modeled in schema/crosswalks)
*real-open · relevance: low · effort: S · section 2159-2782*

grep of crosswalks/body_crosswalk.csv finds no Board of Adjustment / BoA row — the body plumbing genuinely does not exist. Explicitly owner-gated by the entry itself, so it must not be executed unilaterally.

### TODO.md:2411 — Orem (d) — re-crawl orem.gov WP ordinance posts each refresh; upgrade within_source rows toward medium if PMN corroborators surface
*real-open · relevance: low · effort: S · section 2159-2782*

This is a standing routine-maintenance instruction, exactly what the section header says to fold into the quarterly refresh; nothing is currently wrong in the data.

### TODO.md:2414 — Ogden CF (a) — 2025 cycle not yet published by the city; re-fetch once posted
*real-open · relevance: medium · effort: S · section 2159-2782*

grep -c '2025' on ogden_city_council/campaign_finance/index.csv returns 0; the layer covers 2019/2021/2023 only. Real but externally blocked — a researcher asking about 2025 Ogden money gets an empty result that is honest, though the emptiness is not surfaced in gov.db (no CF caveat rows exist at all: SELECT * FROM caveat WHERE dataset LIKE '%finance%' returns nothing).

### TODO.md:2439 — Alta (d) [low] — Whisper leads: 348 SoundCloud tracks + 172 captioned YouTube videos
*real-open · relevance: none · effort: L · section 2159-2782*

Entry is explicitly a proposal ('candidates proposed'). Pure scope expansion; no defect.

### TODO.md:2441 — Alta (e) [low] — pre-2021 ordinances (2020-O-1..O-3) unlocated; 4 none linkages; digit-zero series form
*real-open · relevance: low · effort: S · section 2159-2782*

gov.db fts_ordinance has 50 alta rows (smallest city set), consistent with a thin but honest ordinance layer; the 4 none-tier links are already honest nulls, not wrong values.

### TODO.md:2449 — Emigration Canyon (b) [med] — cf-vision the 35 CF filings + Whisper the 211 PMN MP3s
*partially-done · relevance: low · effort: L · section 2159-2782*

CF half is done — 30 vision/*.json caches, contributions.csv present, 18 cf_cycle rows ($1,167.11). The Whisper/audio half is untouched and remains a scope-expansion option (audio is the only verbatim record for a narrative-tally council).

### TODO.md:2462 — Copperton (a) [low] — pmn_backfill is a complete superset; one OCR-upgrade lead (2025-10-15 born-digital draft vs RICOH scan)
*real-open · relevance: low · effort: S · section 2159-2782*

Entry itself records 0 recoveries and that the approved scan correctly stays canonical (the born-digital copy is only a DRAFT). Marginal text-quality polish.

### TODO.md:2471 — Copperton (d) [low] — R2025-01…08 town-era resolutions not yet on MunicipalCodeOnline (codification lag); re-probe
*real-open · relevance: low · effort: S · section 2159-2782*

gov.db fts_ordinance has 129 copperton rows, so the layer exists; the missing run is an external codification lag. Standing re-probe = quarterly-refresh material, as the section header directs.

### TODO.md:2477 — Magna (a) rider — 2025-11-18 CRA DRAFT rejected; 're-check PMN for an approved copy'
*real-open · relevance: low · effort: S · section 2159-2782*

A one-document watch left behind by an otherwise-completed (✅ 2026-07-16) promotion; correctly rejected for cause (draft), so the current state is honest, not wrong.

### TODO.md:2480 — Magna (b) [med] — cf-vision the 63 CF filings (56 scanned) + Whisper the 370 PMN MP3s
*partially-done · relevance: low · effort: L · section 2159-2782*

CF is built — filing_totals.csv has 74 rows, contributions.csv present, 39 cf_cycle rows ($24,496.20) — though only 17 vision caches exist, so some scanned filings likely came through OCR/text or sit in the owner-gated below-floor tranche (TODO.md:2176). The Whisper half (magna is called the repo's highest-value audio target) is entirely open scope expansion.

### TODO.md:2497 — Kearns (b) [med] — cf-vision the 38 township CF filings + Whisper the 218 PMN MP3s
*partially-done · relevance: low · effort: L · section 2159-2782*

CF half fully done: 38 vision/*.json caches for 38 raw filings, contributions.csv present, 24 cf_cycle rows. Whisper half untouched — scope expansion only.

### TODO.md:2503 — Kearns (d) [low] — blocked CF cycles: 2023 (EasyVote auth-gated) + 2025 city-era (Cloudflare; 11 filings PROVEN to exist)
*real-open · relevance: medium · effort: M · section 2159-2782*

kearns cf_cycle has 24 rows but the entry documents 11 provably-existing 2025 filings that are unfetchable. Relevance is medium because kearns CF totals are knowably incomplete and no gov.db caveat row records that (the caveat table has no finance-dataset rows at all).

### TODO.md:2506 — Kearns (e) [low] — ordinance re-harvest: 26 minute-cited 2025-26 instruments not yet on MunicipalCodeOnline
*real-open · relevance: low · effort: S · section 2159-2782*

fts_ordinance has 223 kearns rows; the shortfall is post-cityhood codification lag at the source. Standing re-probe → quarterly refresh.

### TODO.md:2520 — White City (c) [med] — cf-vision the 2025 CF (18 reports, 15 scanned) + Whisper the 13 MP3s
*partially-done · relevance: low · effort: M · section 2159-2782*

CF half done: 18 vision caches, filing_totals.csv 18 rows, 6 cf_cycle rows ($15,548.08). Whisper half open (13 MP3s) — scope expansion.

### TODO.md:2522 — White City (d) [low] — ~68 minute-cited ordinance numbers not yet on MunicipalCodeOnline (2026 run)
*real-open · relevance: low · effort: S · section 2159-2782*

fts_ordinance carries 136 white_city rows; the rest await the post-HB35 code rewrite at the source. Re-probe item for the quarterly refresh.

### TODO.md:2545 — South Salt Lake (d) [med] — Whisper the cliff-year videos (160 already have ASR captions)
*real-open · relevance: none · effort: L · section 2159-2782*

The entry itself says ASR already exists for the 160 videos and Whisper is only an accuracy upgrade — and the underlying 'cliff' was substantially closed by (a) on 2026-07-16. Optional quality polish.

### TODO.md:2548 — South Salt Lake (e) [low] — 429 packets index-only (3.37 GB); fetch on demand
*real-open · relevance: low · effort: M · section 2159-2782*

Deliberate storage-economy decision with a documented on-demand fetch path (?packet=true). Not a defect.

### TODO.md:2558 — Holladay (c) [med] — Whisper the 75 caption-less SuiteOne 2025-2026 meeting videos
*real-open · relevance: low · effort: L · section 2159-2782*

Genuinely open and genuinely the only video record of the current era, but minutes for the same era exist — no query returns a wrong answer. Scope expansion.

### TODO.md:2560 — Holladay (d) [low] — 102 within_source ordinance rows (motion-attested only; American Legal bot-gated)
*real-open · relevance: low · effort: M · section 2159-2782*

fts_ordinance has 123 holladay rows; within_source is an honest confidence tier already, so the data is correctly labelled rather than wrong.

### TODO.md:2575 — Cottonwood Heights (d) [low] NEW BODY — Architectural Review Commission (PMN 2150, 13 minutes) + Appeals Hearing Officer (7091)
*real-open · relevance: low · effort: M · section 2159-2782*

cottonwood_heights_city_council/CLAUDE.md lines 208/214 record the ARC inventory finding but no dataset exists for it, and body_crosswalk.csv has no ARC row. A real land-use body the repo does not model — but its absence is disclosed, so no answer is wrong, only incomplete.

### TODO.md:2578 — Cottonwood Heights (e) [low] — full transcript harvest (511 videos mapped, ASR on all)
*real-open · relevance: none · effort: L · section 2159-2782*

Scope-expansion option; the map exists in transcripts/ and minutes cover the same meetings.

### TODO.md:2579 — Cottonwood Heights (f) [low] — Ord 392/455/456/457 no citation/PDF; Ord 304 pre-floor
*real-open · relevance: low · effort: S · section 2159-2782*

fts_ordinance has 128 CH rows; four series holes witnessed nowhere are honest gaps rather than errors.

### TODO.md:2589 — Midvale (d) [low] — full transcript harvest (258 videos); iterate yt-dlp player_client for ~3 android_vr false-negatives
*real-open · relevance: none · effort: L · section 2159-2782*

Scope-expansion option plus a 3-file tooling nit; no data defect.

### TODO.md:2591 — Midvale (e) [low] — ordinance gaps: 2 adopted-but-no-PDF, 106 year-only-dated rows, 25 consent-agenda none links
*real-open · relevance: low · effort: M · section 2159-2782*

All three are honest-null conditions already represented as within_source / none-tier / coarse dates rather than fabricated values; 263 midvale ordinance rows are federated.

### TODO.md:2604 — Riverton (c) [low] — Whisper: 652 Granicus clips catalogued; 2025-12-16 mayoral tie-break is the top candidate
*real-open · relevance: none · effort: L · section 2159-2782*

Explicitly a candidate list (transcripts/granicus_clips.csv exists as the map). Scope expansion.

### TODO.md:2610 — Riverton (e) [low] — 301 oversize packet exhibits re-fetchable; 83 legistarweb 2020 exhibits permanently 403
*real-open · relevance: low · effort: M · section 2159-2782*

dropped_oversize.csv gives the recovery path; the 403 set is documented as permanently lost with content surviving in agenda outlines.

### TODO.md:2622 — Draper (c) [med] — election-record notes: 2019 primary scheduled-then-not-held; 2025 canceled 4-yr race CF-corroborated
*real-open · relevance: low · effort: S · section 2159-2782*

gov.db election_race has draper primaries for 2007/2009/2013/2017/2023/2025 but none for 2019, consistent with 'scheduled then not held'; the ask is only to record the explanatory note. Cosmetic provenance improvement.

### TODO.md:2626 — Draper (d) [low] — Whisper candidates (2024-10-15 tie-break, 2026-07-07 recap-only, top v_contested PC dates)
*real-open · relevance: none · effort: L · section 2159-2782*

Self-labelled 'proposed only'; direct MP4 URLs already mapped in transcripts/granicus_clips.csv.

### TODO.md:2629 — Draper (e) [low] — 373 oversize packet exhibits fetchable; 7 dead Legistar URLs; 2024-07-16 CRA has no packet
*real-open · relevance: low · effort: M · section 2159-2782*

Recovery paths recorded in dropped_oversize.csv; HPC/Tree/Arena packets explicitly out of scope.

### TODO.md:2647 — Herriman (d) [med] — bulk caption fetch of the ~51 substantive no-minutes videos (~35 MB)
*partially-done · relevance: low · effort: M · section 2159-2782*

The entry notes the subset shrinks once (a) promotes recovered minutes — and (a) completed 2026-07-16 (66 docs promoted), so the target set is now smaller and partly moot; the residual is an enrichment, not a defect.

### TODO.md:2649 — Herriman (e) [low] — mirror the 1.7 GiB 2020 packet set from the legacy herriman-agendas S3 bucket
*real-open · relevance: low · effort: M · section 2159-2782*

A preservation hedge against a legacy host retiring; keys are already stored in packets/index.csv so the risk is loss-of-source, not present incorrectness.

### TODO.md:2652 — Herriman (f) [low] — 12 ordinance series holes 2020+; 2026-14 postdates minutes; spot-audit the 10 typo-overrides
*real-open · relevance: low · effort: S · section 2159-2782*

fts_ordinance has 278 herriman rows; the overrides are documented in ordinances/build_index.py with verbatim retained. The spot-audit is routine refresh hygiene.

### TODO.md:2665 — Murray (b) [med] — bulk caption fetch of the 86 minutes-gap videos (23 council 2023, 63 PC)
*partially-done · relevance: low · effort: M · section 2159-2782*

The premise was the 2023 minutes gap — which (a) closed on 2026-07-16 (all 18 missing 2023 council + 59 PC minutes promoted; only PC 2025-04-17 and 2025-07-17 remain minute-less). The video captions are now a redundant secondary record for all but 2 dates.

### TODO.md:2672 — Murray (e) [low] — ordinance text gaps (2020→Apr-2021 unpublished, O22-02, O22-30/O23-14, O26-15 mis-upload); '17 none linkages resolve when (a) promotes 2023 minutes'
*partially-done · relevance: low · effort: S · section 2159-2782*

(a) completed 2026-07-16 and its closure note states ordinance none-links went 18→0, so the dependent clause is already satisfied; the residual unpublished-text items are external-source watches. fts_ordinance carries 172 murray rows.

### TODO.md:2690 — Taylorsville (b) [med] — consider merging the 2 recovered 'Let's Talk Taylorsville' town halls (2020-01-29, 2024-01-31)
*real-open · relevance: low · effort: S · section 2159-2782*

Entry describes them as real council-body meetings with no roll-call votes, sitting in pmn_backfill/. Merging adds context documents only — no vote/motion answer changes, and the decision is framed as 'consider'.

### TODO.md:2702 — Taylorsville (c)(ii) — replace inferred filing `date`s with the PDF 'Received' stamps
*unverified · relevance: low · effort: S · section 2159-2782*

I did not open the individual PDFs to check whether stamps were later transcribed; the index carries 71 filings and no date-provenance column was inspected. Affects only date-precision on CF filings, never cycle totals (which come from cf_cycle).

### TODO.md:2702 — Taylorsville (c)(iii) — re-probe the 2025 CF page for not-yet-posted election-cycle filings (2019 cycle never posted)
*real-open · relevance: low · effort: S · section 2159-2782*

taylorsville has only 8 cf_cycle rows ($20,127.41) — the thinnest CF layer of the 29 — consistent with unposted cycles at the source. A standing re-probe for the quarterly refresh.

### TODO.md:2703 — Taylorsville (d) [med] — real transcripts via OpenUtah/Whisper (audio-only city, Whisper NOT run)
*real-open · relevance: low · effort: L · section 2159-2782*

Genuinely open (1 ASR sample only; OpenUtah robots-limited), but minutes exist for the same meetings, so it is enrichment rather than correction.

### TODO.md:2709 — Taylorsville (f) [low] — ordinance refresh (re-crawl PMN body 720, diff vs index.csv) + ~129-doc 2012–2019 back-catalog
*real-open · relevance: low · effort: M · section 2159-2782*

fts_ordinance has 90 taylorsville rows; the back-catalog is explicitly conditional on lowering the 2020 floor (a scope decision, not a defect). Re-crawl = quarterly-refresh routine.

### TODO.md:2740 — [OPTION] Transcript backfill (Provo 740 videos, West Jordan 647, Orem 111, Lehi URL-map only)
*real-open · relevance: none · effort: L · section 2159-2782*

Explicitly tagged [OPTION] with an owner ruling already recorded ('transcripts SAMPLE-ONLY going forward'). It is a decided scope boundary, not a defect — keep as an option, do not queue.

### TODO.md:2776 — PMN cross-check rider — 'Revisit the 60-day pending-adoption window after 2–3 refresh cycles'
*real-open · relevance: low · effort: S · section 2159-2782*

Only one full quarterly refresh has run (Q3-2026, 2026-07-19), so the 2–3 cycle precondition is not met yet; this is a parameter-tuning watch inside an otherwise-closed [x] entry. Correctly deferred to October 2026 and beyond.

### TODO.md:2822 — CF wave (g) residual — below-floor / pre-2020 vision tranches
*real-open · relevance: low · effort: M · section 2783-3495*

Named sets: murray 2017/2019 x28, magna 2016-2019 x43, alta/holladay 2017 handfuls, kearns 2023/2025 (EasyVote auth / Cloudflare). Checked magna_city_council/campaign_finance/vision/ = 17 caches (the above-floor bundles only). These are explicitly BELOW each city's data floor or behind auth walls, so their absence produces no wrong answer inside the published window — cf_cycle (805 rows / 29 cities) covers the in-floor cycles.

### TODO.md:2864 — New acquisition lead — bluffdale Robbins itemizing Oct-26 2021 pre-general filing absent from index
*real-open · relevance: low · effort: S · section 2783-3495*

bluffdale_city_council/campaign_finance/index.csv has 3 Robbins rows, none dated Oct-26 2021 — confirms the absence. The $5,619.41 unitemized block is documented as the FILING'S OWN gap (line 2964-2969), so the repo is already honest about it; acquiring the missing report only adds itemization detail.

### TODO.md:2878 — CF follow-up (d) — acquisition riders (CH Prazen final, riverton Pierucci, kearns 2023/2025, magna 2023)
*real-open · relevance: low · effort: M · section 2783-3495*

All four are EXTERNAL acquisitions (recorder request, state mis-publication, EasyVote auth, Cloudflare), not repo defects; each is already ledgered honestly in its city's campaign_finance docs. Note this bullet is DUPLICATED verbatim as WAVE-2 follow-ups (d) at line 3007 and (e) at line 3009 — the same two leads live in two entries.

### TODO.md:2883 — [GATED] OWNER HAND-CHECK of the 2026-07-18 CF adjudications (11 figures)
*real-open · relevance: low · effort: M · section 2783-3495*

Verified every adjudicated figure is LIVE and matches the entry exactly: gov.db cf_cycle holladay Tracy 4389.17/3924.19, Watts 65135.33/62880.49, Wilson 38914.37/27017.01, bluffdale Hall 22135.67/18471.66; herriman cycle_overrides.csv rows 4-5 carry Smith 28610.56/28635.96 and Palmer 32038.06/31782.48 with cited ADJUDICATED evidence notes. This is an owner EYEBALL of already-evidenced, already-overridable numbers — not a defect. Its only genuinely unresolved content is owner questions (i)/(ii), triaged separately at line 2859.

### TODO.md:2989 — WAVE-2 (a) — GRAMA queue (owner-gated outreach for ~100 unpublished minutes across 13 cities)
*real-open · relevance: low · effort: L · section 2783-3495*

64 minutes_unrecovered.csv ledgers exist across the repo and bluffdale_city_council/pmn_backfill/GRAMA_request_draft.md is present as claimed. Every target date is already recorded as an honest gap (cardinal rule 1), so nothing in gov.db is wrong — this only raises completeness, and it is gated on third-party records officers (weeks of latency, outside the publish path).

### TODO.md:3003 — WAVE-2 (c) — Whisper/audio transcription leads (st_george, taylorsville, copperton, magna, alta)
*real-open · relevance: none · effort: XL · section 2783-3495*

This is a lead-list feeding an owner-gated Whisper PROGRAM (audio -> transcript -> a new derived layer), i.e. pure scope expansion into a source type the repo does not yet claim. No published figure is wrong because it is open; the affected dates are ledgered as unrecovered minutes.

### TODO.md:3007 — WAVE-2 (d) — riverton Pierucci genuine 10-24-23 report re-acquisition
*real-open · relevance: low · effort: S · section 2783-3495*

Duplicate of the CF acquisition rider at line 2878. External (state mis-publication); the index row is annotated pending, so the repo does not assert anything false about it.

### TODO.md:3009 — WAVE-2 (e) — CH Prazen genuine final CF report (recorder request)
*real-open · relevance: low · effort: S · section 2783-3495*

Duplicate of line 2878's rider and of the CH duplicate_of work at line 2810-2812, where the posted 'final' is already labelled a re-upload of the Oct-28 interim with the genuine final marked a gap — the honest record is in place.

### TODO.md:3013 — WAVE-2 (g) — fetch_new hardening idea: Wayback-listing sweep for delisted-but-served CMS docs
*real-open · relevance: none · effort: M · section 2783-3495*

Explicitly phrased as an 'idea' for the acquisition harness, not a defect; the CH instance it generalizes from was already recovered (line 3293, 'delisted-but-live CMS docs via Wayback listing anchors'). Affects only future refresh yield, never a published value.

### TODO.md:3015 — WAVE-2 (h) — west_jordan PC roster regeneration over the merged 2020+ span (optional)
*unverified · relevance: low · effort: S · section 2783-3495*

west_jordan_city_council/roster/ exists (council_terms.csv, district_versions.csv, roster_overrides.csv, AUDIT.md) but the roster layer is a COUNCIL roster by design — the item concerns the db-side PC member first_seen bounds now that 27 recovered 2020-21 PC meetings extend below the 2022 audited floor. Self-labelled optional; affects only PC member-tenure bounds in one city.

### TODO.md:3018 — WAVE-2 (i) — pending re-checks next refresh (magna CRA x3, st_george PC 2026-03-10, vineyard x2)
*real-open · relevance: low · effort: S · section 2783-3495*

These are pending-adoption watches — minutes that did not exist yet at wave time. They resolve automatically in the Q4-2026 refresh (next run recorded as first week of October 2026, line 2766). Not a defect; the dates are ledgered.

### TODO.md:3021 — WAVE-2 (j) — magna lower-confidence crosscheck flags not worked (deliberate scope cut)
*not-an-issue · relevance: none · effort: S · section 2783-3495*

Self-describes as a 'deliberate scope cut', and the entry itself notes magna's PC is 'a documented complete superset' — so the two PC flags cannot be real gaps. Six low-confidence council/PC flags in one city, already reasoned about; keeping as a lead is fine but it should not be read as owed work.

### TODO.md:3116 — LM wave (l) [owner Q] — copperton 2025 seat lettering (HB35 town-era re-lettering unresolved)
*real-open · relevance: low · effort: S · section 2783-3495*

Verified documented in copperton_city_council/roster/CLAUDE.md lines 31-32 and 83-84: 'The person-chains are consistent, but the town-era HB35 seat-lettering (does Pratt hold C or E?...)' is explicitly flagged. Person-level roster answers (who served when) are correct; only the seat LABEL for a ~800-person town is ambiguous, and the ambiguity is disclosed in the authoritative per-city doc.

### TODO.md:3146 — LM wave (o) — six-city prior-geometry acquisition (2019/2020 SLCo VistaBallotAreas snapshot)
*real-open · relevance: medium · effort: L · section 2783-3495*

The risk it addresses is already FENCED by lead (c) (line 3089): all six pre-2022 dissolve reconstructions were downgraded to LOW with cited notes after millcreek proved the method can be materially wrong (IoU 0.00-0.25), and lead (j) (line 3109) made representatives_for_address confidence-GATED so low geometry does not silently resolve. So a researcher asking a pre-2022 address->district question in those 6 cities gets an honest gap, not a wrong answer. Acquisition is external (unpublished county snapshot).

### TODO.md:3263 — Q3 refresh (g) — SSL design question (owner): vote-less work-meeting minutes ARE published to PMN but the residual ledgers them 'minutes-not-posted'
*real-open · relevance: medium · effort: M · section 2783-3495*

Unverified at source but internally consistent with south_salt_lake's own record (root CLAUDE.md: 'residual = 214 genuinely-unpublished dates, mostly council WORK meetings'; line 3330 recounts 214->221). If those dates are in fact PUBLISHED-but-vote-less, SSL's headline coverage claim overstates the gap — a misleading coverage answer in exactly the city whose 'coverage cliff' is most discussed. Owner design decision gates it.

### TODO.md:3266 — Q3 refresh (h) — smaller items (draft watches, copperton ord roll, SJ OCR hardening, millcreek CRA, EC PC, ogden 'AYE —' OCR anchor, provo/lehi packet windows)
*real-open · relevance: low · effort: M · section 2783-3495*

Mixed grab-bag; most entries are next-refresh watches that resolve automatically. The one with real data impact is the ogden "AYE —" OCR anchor variant (an unhandled anchor can leave named votes unextracted as tally-only), and SJ transcript-style-OCR motion-text hardening; both are single-city extraction polish, not cross-repo correctness.

### TODO.md:3284 — [~] PMN-crosscheck RECOVERY LEADS — the verified inventory
*partially-done · relevance: low · effort: M · section 2783-3495*

The entry's own header says both worked tiers are CLOSED ('REAL MINUTES ON PMN' promoted; AGENDA-GRADE 'WORKED TO ZERO OPEN FLAGS across all 16 flagged cities') and that 'What REMAINS below is only the owner scope decisions + the ingestion-side items (now done)' — yet lines 3300-3318 still print both closed inventories as live bullet lists. The [~] is honest only for the scope-decisions bullet (line 3319, triaged separately); the rest is a historical ledger presented as open work.

### TODO.md:3319 — PMN inventory — SCOPE DECISIONS for the owner: lehi advisory-committee bodies; orem RDA/MBA/BoA promotion (22 recovered docs)
*not-an-issue · relevance: low · effort: M · section 2783-3495*

The stated premise 'orem RDA/MBA/BoA ... (22 recovered docs, NO REPO LAYER)' is WRONG: gov.db already carries orem bodies Council 569 / PlanningCommission 501 / RDA 42 / MBA 9 / SSLD 17 motions, so orem HAS an RDA/MBA layer (from combined minutes); the 22 PMN docs are additional standalone meeting documents, and orem_city_council/pmn_backfill/ holds 43 retained files. Promotion would deepen an existing layer, not create a missing one — a scope OPTION, not a gap.

### TODO.md:3390 — [TAIL/routine] Re-run /audit-city-data periodically (or after any large ingest)
*real-open · relevance: none · effort: M · section 2783-3495*

Confirmed the harness exists (.claude/skills/audit-city-data listed in the session's skill roster; _audits/ holds dated reports, e.g. _audits/2026-07-25/, 2026-07-19-postingest-{ogden,park_city}/). This is a standing MONITORING routine with no defect behind it — it can never be 'done' and should be recorded as a cadence item, not an open checkbox.

### TODO.md:3498 — Taylorsville CF: 47 mandatory-annual March-1 statements acquired but itemization deferred
*real-open · relevance: low · effort: M · section 3496-3786*

Entry is [x] but its body carries a live residual: the 47 mandatory-annual filings were acquired and NOT itemized (deliberately excluded from race totals). gov.db cf_cycle has 8 taylorsville rows and cf_contribution 103 — small but present and regime-filtered as the note says. A researcher gets correct election-cycle totals; the annual stream is an additive future layer, not a wrong answer.

### TODO.md:3604 — Holladay — recover PC 2020/2021/2023 minutes (89 rows in minutes_unrecovered.csv)
*partially-done · relevance: low · effort: L · section 3496-3786*

Root CLAUDE.md records that PC 2020 H1 + 2021 H1 were recovered 2026-07-16 via Wayback (provenance='wayback_minutes'); /Users/tysonwelsh/civic-data/holladay_city_council/planning_commission/minutes_unrecovered.csv is now 63 data rows (2020:7, 2021:10, 2022:8, 2023:19, 2024:2, 2025:10, 2026:7), down from the filed 89. The 2020 H2 / 2021 H2 / 2023 residue is documented as dead on every channel. Honest, documented, machine-readable gap — a researcher is told, not misled.

### TODO.md:3626 — Bluffdale — 2 land-use ordinances with match_confidence='none' (2020-06 signs, 2023-29 Draper boundary)
*real-open · relevance: low · effort: S · section 3496-3786*

Verified in /Users/tysonwelsh/civic-data/bluffdale_city_council/ordinances/index.csv: exactly 2 rows with land_use='yes' AND match_confidence='none' — ordinance_no 2020-06 ('TEMPORARY LAND USE REG...') and 2023-29 ('ADJUSTMENT OF A COMMON ...'). Unlinked ordinances are an honest NULL in the ordinance→motion join (docs already say never quote ambiguous links), so no wrong answer results — 2 of 150.

### TODO.md:3642 — Bluffdale — LBA motions carry stage='mba_vote' (cosmetic bucket reuse)
*real-open · relevance: low · effort: S · section 3496-3786*

gov.db confirms 22 bluffdale motions with stage='mba_vote' and no lba_vote stage. The body split (Council/RDA/LBA) is correct, so filtering by body_id gives the right answer; only a stage-based filter mislabels 22 motions. The entry already documents the workaround.

### TODO.md:3656 — Kearns — 2022-11-14 '11-14-22.pdf' mis-filed under PMN category 'Audio Recording'; verify + promote if it is minutes
*unverified · relevance: low · effort: S · section 3496-3786*

Repo state CONTRADICTS the edge case: /Users/tysonwelsh/civic-data/kearns_city_council/meeting_minutes/minutes_unrecovered.csv line 30 asserts for 2022-11-14 that PMN body 5823 'posted only an agenda and MP3 audio ... NO written Meeting Minutes attachment was ever published.' The TODO says a date-named PDF sits under the wrong category. One of the two is wrong and I cannot adjudicate read-only (needs a PMN fetch of notice 793979). One meeting; the CSV records it as an honest gap either way.

### TODO.md:3678 — Kearns — fold PC person 'Thomes'(1) → 'Thomas' (Gray Thomas)
*real-open · relevance: low · effort: S · section 3496-3786*

One occurrence remains, at /Users/tysonwelsh/civic-data/kearns_city_council/planning_commission/all_votes.csv:160 (2025-03-03 m8 'to adjourn', mover='Thomes'). It is a MOVER cell on a tally-only motion with blank member/vote, so it created no person row — gov.db kearns has only 'Thomas' (2 votes). Cosmetic; affects no vote aggregation.

### TODO.md:3687 — Copperton (a) — enrich minutes_unrecovered.csv 'candidates' with real purged PMN file-IDs
*real-open · relevance: low · effort: S · section 3496-3786*

Verified still guessed filenames: /Users/tysonwelsh/civic-data/copperton_city_council/meeting_minutes/minutes_unrecovered.csv rows carry candidates='pmn:02-15-17.pdf:empty/small', not the audit-surfaced numeric IDs (315659, 413287). The reason column already states the 404/retention-purge verdict correctly, so the gap is honestly explained; this is provenance polish only.


## Close as done (stale entries — the work already landed) (62)

### TODO.md:355 — *(original)* cache_county 12 un-indexed duplicate minutes — text still says "NOT fixed"
*stale-already-done · relevance: none · effort: S · section 43-560*

This *(original)* block (lines 349–358) is verbatim pre-fix text that (h3) at lines 318–340 already closed (index-driven extraction; motions 3,495→3,388). gov.db confirms the post-fix figure: cache_county motion count = 3,388. Pure stale bookkeeping sitting under an open checkbox where a future session could act on it a second time — delete or fold into the (h3) note.

### TODO.md:359 — *(original)* "Ordinance links contradicted by primary documents — STILL OPEN (cache)"
*stale-already-done · relevance: none · effort: S · section 43-560*

Line 361 literally reads **STILL OPEN (cache)** but items (h) (lines 248–274) and (h3) (lines 334–340) closed it: cache_county/db/link_ordinances.py exists on disk and produced 17 derived `high` links that survived the motion_id renumbering. The 'STILL OPEN' string is the single most misleading line in the range for anyone triaging by grep.

### TODO.md:399 — TIER 3 "Still open:" list — wfrc marks/result_raw, cache Sands, weber 9 dropped votes, summit sidecars
*stale-already-done · relevance: none · effort: S · section 43-560*

Lines 399–408 re-list as open six things the SAME TIER-3 paragraph marks ✅ done at lines 369–398. Verified each: 0 wfrc minutes files contain U+202A-E/U+2066-9 (grep -rlP over wfrc_mpo/legislative/minutes); 0 wfrc motions with result_raw LIKE 'ith %'; cache Chris Sands now carries votes on 8 of 9 motions at 2024-11-07; weber CSV-vs-db delta is the itemized 9 (12,594 flat vs 12,585 db); summit sidecar residual is the documented 4 CAD-text files. Only the washington and mag entries in this list are still real (separate rows).

### TODO.md:462 — (k) coverage.json covers only cities
*stale-already-done · relevance: none · effort: S · section 43-560*

Premise fails: coverage.json (mtime 2026-07-29, as_of '2026-07-29', generated_by scripts/build_coverage.py) carries an `entities` block with all 44 slugs including every county, both MPOs, ut_state and the registered-only udot/uta, plus entity_counts {total 44, built 41, registered_only 3, by_level city 31/county 8/regional 2/state 3} and per-entity caveat text (checked cache_county's entry). The legacy 31-key `cities` block is retained for back-compat. Item was closed by the 07-29 rebuild and never checked off.

### TODO.md:520 — TIER 5 — cache_county legislative raw retention (⏳ PENDING OWNER DECISION)
*stale-already-done · relevance: none · effort: S · section 43-560*

The recommended option (b) has already been executed and documented: /Users/tysonwelsh/civic-data/cache_county/legislative/raw/ now exists with exactly 25 PDFs totalling 150 MB (the dead-URL / wayback-recovered slice), and cache_county/CLAUDE.md:75 and :227 describe it as 'a DELIBERATE 25-of-305 SLICE (150 MB): only the dead-URL documents'. The provenance half is likewise verifiable on disk (legislative/wayback_snapshots.csv with snapshot_url/snapshot_timestamp columns; legislative/recover_snapshots.py). Nothing is owed; the ⏳ marker is stale.

### TODO.md:1157 — Phase 2 follow-up — re-point the 7 SLCo cities' election pipelines at the county canonical (true dedup)
*stale-already-done · relevance: none · effort: S · section 1125-1557*

Checked on disk: /Users/tysonwelsh/civic-data/slc_city_council/election_results/ has NO raw/ dir (slice deleted), taylorsville retains only raw/sovc for the 2019/2021 generals as documented, and the entry's own text records slc/sandy/wj/wvc/sj/taylorsville all DONE 2026-07-19 with millcreek a documented永 exception; the only thing left is the millcreek 2016 even-year SOVC unblock, which is recorded as an intentional exception, not work.

### TODO.md:1219 — Phase 3 — Salt Lake County full build (marked [~])
*stale-already-done · relevance: none · effort: S · section 1125-1557*

All three items in its own 'NEXT:' list are satisfied — /Users/tysonwelsh/.claude/skills/build-county-data-repo/SKILL.md exists (Phase 3c), salt_lake_county/CLAUDE.md refresh is recorded DONE at TODO.md:1333, and Phase 4 shipped; the only survivor is the county content menu, which is separately tracked at TODO.md:1492 and 1519-1549, so the [~] is duplicate bookkeeping.

### TODO.md:1498 — Phases 4–6 residual (2) — post-build audits for the 9 new entities (marked ✅ DONE 2026-07-25)
*stale-already-done · relevance: none · effort: S · section 1125-1557*

_audits/2026-07-25/ exists and its downstream fix — the utah_county vote-layer repair — is recorded DONE at TODO.md:129-130 with motions 10,089→11,218, which gov.db independently confirms (utah_county = 11,218 motions); the closure note is sound, though see section_summary: root CLAUDE.md still carries the pre-repair ⚠ warning about utah_county, which is now the misleading artifact.

### TODO.md:1513 — Phases 4–6 residual (3) — /build-county-data-repo skill lesson absorption (referral table, ordinances motion_id, link-only rows, md_path, PMN JSON-POST)
*stale-already-done · relevance: none · effort: S · section 1125-1557*

All five named lessons are already in ~/.claude/skills/build-county-data-repo/SKILL.md: referral-table-required at line 241, ordinances index.csv motion_id at 121, link-only catalog rows at 124, md_path canonical at 119-120, and the PMN JSON-POST + X-CSRF-TOKEN channel at 143-144 — the entry says they are 'NOT yet folded into the skill text' and that premise is simply false now.

### TODO.md:1539 — County menu — population/housing projections by year × sub-county geography
*stale-already-done · relevance: none · effort: S · section 1125-1557*

gov.db `projection` holds 980 county rows (140 × 7 counties, Gardner v2025+v2022) plus 9,832 regional and 140 state — the Phase-4 shared projections agent delivered exactly this menu item, and leaving it checkbox-open in the menu misrepresents the repo's actual coverage.

### TODO.md:1541 — County menu — General Plan / township GP / small-area plans + Moderate-Income Housing corpus
*partially-done · relevance: none · effort: M · section 1125-1557*

Every db-carrying county already has a plans/ module with a populated index.csv — salt_lake_county 14 (5 MIH rows), washington 24, summit 10 (8 MIH), cache 7 (1), weber 5 (0), utah 2 (2) — so the corpus exists at varying depth; only weber's zero-MIH row count is a residual, which is better tracked as a weber-specific gap than as an unbuilt menu module.

### TODO.md:1658 — Election URL provenance — 'NOT DONE (deferred, minor)' 33 residual unrecorded rows + 3 pointer-less cities
*stale-already-done · relevance: none · effort: S · section 1558-1920*

This is a nested 'NOT DONE' block inside the [x] entry at line 1620, but it is itself closed immediately below at lines 1667-1696 ('✅ DONE 2026-07-20 (P4 URL residue) … 0 `unrecorded` election rows remain across the 9 touched cities; all 9 validate 0 FAIL'), with per-city sha256/md5 verification records for sandy, south_jordan, taylorsville, west_jordan, west_valley, murray, emigration_canyon, kearns. No open work; the nested NOT-DONE header is stale text that reads as open on a skim.

### TODO.md:1709 — Alta 2025 municipal election missing from the canonical SLCo file
*not-an-issue · relevance: low · effort: S · section 1558-1920*

Premise REFUTED at source. alta_city_council/election_results/alta_races.csv lines 5-6 already carry the 2025 Mayor and Council At-Large rows, recorded 2026-07-17 (file mtime Jul 19 22:07), with winners ROGER BOURKE / CAROLYN ANCTIL + CRAIG HEIMARK and note 'cancelled_certification (Utah Code 20A-1-206; Res 2025-R-26)'. alta_city_council/roster/council_terms.csv line 4 states it explicitly: 'NOT a county-file gap where the election occurred (that earlier framing is SUPERSEDED — the election was cancelled, so no votes exist)'. The prescribed action ('re-pull the raw 2025 SOVC when available') is therefore impossible and unnecessary — no Alta contest will ever appear in a SOVC. Also a DUPLICATE of the same claim at TODO.md:2432 sub-item (b) of the Alta expansion entry, which is likewise stale.

### TODO.md:1731 — v_contested_all redefinition — two follow-ups (tally_other semantics; per-city v_contested column shape)
*stale-already-done · relevance: none · effort: S · section 1558-1920*

[x] item whose closure I spot-checked and CONFIRMED both halves. (1) cities_db_SCHEMA.md:257 carries the section 'tally_other semantics (audited at source 2026-07-19 — BY DESIGN)' explaining NULL-not-0 encoding and the COALESCE fallback, ground-truthed across 9 cities. (2) scripts/db_build_lib.py v_contested now emits the split shape — tally_aye/tally_nay/tally_other (line ~382, COALESCE from motion_std at ~461) alongside named_ayes/named_nays (~464) with the MARGINS/ATTRIBUTION comment block at ~447-457, i.e. the federated shape is mirrored per city. Nothing open.

### TODO.md:1744 — Full-name voter-resolution audit — entry marked COMPLETE but body still lists 'STILL TODO' (a) taylorsville/west_valley (b) st_george PC (c) vineyard PC
*stale-already-done · relevance: none · effort: S · section 1558-1920*

Self-contradicting entry: the [x] header says all three done 2026-07-19, lines 1750-1756 still say 'STILL TODO'. Verified the CODE, and the header is right: taylorsville_city_council/meeting_minutes/extract_votes.py:72 has 'First-name index for the SAFE full-name gate (memory: prefer-full-name-vote-resolution)'; west_valley's canon_last (~line 265) returns None whenever SURNAME_TO_FULLS holds >1 candidate; st_george_city_council/planning_commission/extract_votes.py:125-146 documents the 2026-07-19 attendance-based Anderson resolution that 'ABSTAINS' on a bare token, explicitly 'replacing the old year GUESS'; vineyard's resolver (lines 105-109) returns the un-merged surname 'Blackburn' rather than defaulting to Tim. Delete the stale STILL-TODO paragraph — leaving it makes a real, closed hardening pass look open.

### TODO.md:1798 — Ogden referral guard — sub-note: federated Ogden referral rows stale until a federation rebuild
*stale-already-done · relevance: none · effort: S · section 1558-1920*

Read-only SQL disproves the stale-federation warning: `SELECT count(*) FROM referral WHERE city='ogden'` on gov.db returns 6, byte-for-byte matching ogden_city_council/db/civic.db's own `SELECT count(*) FROM referral` = 6. gov.db mtime is Jul 29 03:01, after the 2026-07-20 port, so the federation window the note asked for has already occurred. Remove the warning so nobody re-runs a rebuild for it.

### TODO.md:1885 — Millcreek geo: source pre-2022 (2016) district boundaries — closed as promoted medium→high
*stale-already-done · relevance: none · effort: S · section 1558-1920*

Spot-checked the closure because the note claims an authoritative layer replaced a reconstruction: millcreek_city_council/roster/district_versions.csv shows plan_2016 rows for Districts 1-4 all at confidence=high (alongside plan_2022 high), matching the claimed promotion. Closure is real. Its spillover lead — 'validation lead (c) queued for the other reconstructed cities' — did get executed, visible as the 2026-07-19 fragmentation-control validation recorded in the slc and west_valley district_versions notes.

### TODO.md:2098 — Buried rider in the closed cottonwood_heights entry: "federated cities.db now stale for CH — regenerate in the next federation pass"
*stale-already-done · relevance: none · effort: S · section 1921-2158*

TODO.md:2098-2100 leaves an un-checkboxed NOT-DONE rider inside an [x] item. Verified it has since landed: gov.db build_info `built_at` = 2026-07-29T03:00:31 (after the 2026-07-20 CH fix), and CH reconciles exactly db-vs-disk — gov.db `SELECT count(*), sum(seconder_person_id IS NOT NULL) FROM motion WHERE city='cottonwood_heights'` = 1468 / 1430, against the on-disk all_votes.csv distinct (source,motion_no) counts of 1161+307 = 1468 motions and 1130+300 = 1430 with a seconder, i.e. the +67 recovered PC seconders are federated. Nothing to do; the rider should simply be struck so it stops reading as open work.

### TODO.md:2156 — Notes: riverton/EC roster layers gain new vote evidence at re-federation
*stale-already-done · relevance: none · effort: S · section 1921-2158*

This is a passive bookkeeping note about something that happens automatically at the next federation, and federation has since run: gov.db build_info `built_at` = 2026-07-29T03:00:31, and the roster layer is populated for both entities (`SELECT city, count(*) FROM term` → riverton 17, emigration_canyon 18). Whether any individual term's `confidence` was upgraded on the strength of the new Stewart/Wells Jan–Feb 2020 vote evidence is unverified (I did not diff pre/post confidence), but nothing is broken or misleading either way — close it.

### TODO.md:2287 — Nephi rider — 'cities.db needs a build_cities_db.py run to reflect the +57 motions (not run here)'
*stale-already-done · relevance: none · effort: S · section 2159-2782*

On disk nephi_city_council/meeting_minutes/all_votes.csv = 989 distinct (source,motion_no) motions; gov.db motion for city='nephi' = 988 Council + 1 CRA = 989. Federation is current; the rider is satisfied.

### TODO.md:2320 — Vineyard (b) rider — 'ordinances/index.csv change reaches cities.db ordinance table only on the next build_cities_db.py run'
*stale-already-done · relevance: none · effort: S · section 2159-2782*

gov.db ordinance for vineyard: 2021-12 → matched_motion_date 2021-09-08, motion_no 4, confidence 'high'; 2021-02 → 2021-02-10 #4. The MOTION_ORD_OVERRIDE fix is federated.

### TODO.md:2432 — Alta (b) [high] — 2025 general entirely absent from alta_races.csv; re-pull the raw 2025 SLCo SOVC
*stale-already-done · relevance: none · effort: S · section 2159-2782*

alta_city_council/election_results/alta_races.csv now carries both 2025 rows (Mayor ROGER BOURKE; Council At-Large CAROLYN ANCTIL + CRAIG HEIMARK) with a cancelled_certification note citing Utah Code 20A-1-206 / Res 2025-R-26. The entry's proposed method was also wrong — the election was cancelled, so no SOVC exists; the box is unticked though the work landed.

### TODO.md:2437 — Alta (c) [med] — cf-vision-transcribe the 36 CF filings (29 scanned)
*stale-already-done · relevance: none · effort: S · section 2159-2782*

alta_city_council/campaign_finance/ has contributions.csv + 21 vision/*.json caches, and gov.db cf_cycle has 13 alta rows totalling $11,725.11. Superseded by the CF-STRUCTURING PACKAGE closed at TODO.md:2170.

### TODO.md:2445 — Emigration Canyon (a) [med] — 2019 council cycle missing from election_results; roster fix 'Griffith was appointed, not elected'
*stale-already-done · relevance: none · effort: S · section 2159-2782*

BOTH halves landed: gov.db election_race has an emigration_canyon 2019 municipal general Council At-Large row, and roster/council_terms.csv line 4 records Nicholas Griffith with method 'appointed', confidence 'high', citing the 2026-01-20 written-ballot minutes. Unticked box, completed work.

### TODO.md:2457 — Emigration Canyon (e) [low] — 'build out the empty core scaffolds: elections/geo/public_comments/db were never built'
*stale-already-done · relevance: medium · effort: S · section 2159-2782*

ls emigration_canyon_city_council/ shows db/civic.db, geo/ (address_to_district.py, precincts.geojson, city_boundary.geojson), public_comments/, election_results/ (5 rows in gov.db election_race), plus weeks/ and roster/. The premise fails. Relevance is medium not none because EC's own CLAUDE.md still says the repo is partial (root CLAUDE.md already flags this staleness) — an outside reader of that file is told the entity is thinner than it is.

### TODO.md:2467 — Copperton (c) [med] — cf-vision the 19 township CF filings; election flag: 2019 A/B/C council cycle missing (re-parse raw 2019 SOVC)
*stale-already-done · relevance: none · effort: S · section 2159-2782*

CF: 19 vision/*.json caches (= all 19 filings), contributions.csv present, 14 cf_cycle rows. Elections: gov.db election_race has three copperton 2019 municipal general Council At-Large rows. The roster half was already REFUTED inline on 2026-07-19. All three sub-claims are closed; only the seat-LETTERING owner question survives and it is tracked in the LM-wave section (duplicate bookkeeping).

### TODO.md:2483 — Magna (c) [med] — election double-gap: 2023 D1/D3/D5 missing from finance AND magna_races.csv; also the 2016/2019 D1/D3/D5 gap
*stale-already-done · relevance: none · effort: S · section 2159-2782*

gov.db election_race: magna 2023 municipal general has Council D1, D3, D5; 2019 has D1, D3, D5; 2016 has D1–D5. The claimed election gap no longer exists (the finance-side EasyVote block is a separate, external matter).

### TODO.md:2488 — Magna (e) [low] SKILL BUG — polite_fetch.py --batch mangles comma-bearing filenames (silent .pdf drop)
*stale-already-done · relevance: none · effort: S · section 2159-2782*

.claude/skills/expand-city-sources/scripts/polite_fetch.py lines 210–218 now parse each batch line with csv.reader and explicitly handle the unquoted comma-bearing-name case; the pre-fix copy survives as _backups/2026-07-16-minutes-promotion/_root/polite_fetch.py.pre-comma-fix. Fixed but never checked off.

### TODO.md:2544 — South Salt Lake (c) [med] — cf-vision the 68 CF filings (54 scanned) + run cycle_totals
*stale-already-done · relevance: none · effort: S · section 2159-2782*

53 vision/*.json caches, contributions.csv present, 24 cf_cycle rows ($169,839.22) — cycle_totals has clearly been run. Superseded by the CF-structuring package.

### TODO.md:2557 — Holladay (b) [med] — cf-vision the 40 CF filings (39 scanned)
*stale-already-done · relevance: none · effort: S · section 2159-2782*

36 vision caches, contributions.csv present, 18 cf_cycle rows ($189,469.98). Done under the CF-structuring package.

### TODO.md:2563 — Holladay (e) [low] — 2019 general gap (D2/D4/D5): re-parse raw 2019 SOVC; CF corroborates the 2025 3-way mayoral primary
*stale-already-done · relevance: none · effort: S · section 2159-2782*

gov.db election_race holladay 2019 municipal general now has Council D2, D4 and D5 rows (plus two 2019 primary rows), and a 2025 municipal primary row exists. Both named leads are satisfied.

### TODO.md:2570 — Cottonwood Heights (b) [med] — 2019 D1 primary the docs say didn't happen; McHugh absent; confirm 2023 D2 3rd candidate (Bracken)
*stale-already-done · relevance: none · effort: S · section 2159-2782*

gov.db election_race has cottonwood_heights 2019 municipal primary Council D1 with n_candidates=3 and a note reading 'Case 578 / Petersen 511 / McHugh 189 — recovered by the 2026-07-16 SLCo SOVC re-parse. CORRECTS the prior CLAUDE claim of no 2019 CH primary'; the 2023 municipal primary Council D2 row shows n_candidates=3. Both halves done.

### TODO.md:2574 — Cottonwood Heights (c) [med] — cf-vision the 86 CF filings (55 scanned)
*stale-already-done · relevance: none · effort: S · section 2159-2782*

58 vision caches, contributions.csv present, 31 cf_cycle rows ($288,652.07).

### TODO.md:2586 — Midvale (b) [med] — cf-vision the 84 CF filings (57 scanned)
*stale-already-done · relevance: none · effort: S · section 2159-2782*

57 vision caches (exactly the 57 scanned claimed), contributions.csv present, 38 cf_cycle rows ($90,313.46).

### TODO.md:2587 — Midvale (c) [med] — load ordinances into fts_ordinance on the next federated rebuild (263 rows / 182 land-use)
*stale-already-done · relevance: none · effort: S · section 2159-2782*

SELECT city,count(*) FROM fts_ordinance GROUP BY city returns midvale = 263 — exactly the claimed row count. The federated load happened; the box was never ticked.

### TODO.md:2603 — Riverton (b) [med] — cf-vision the 60 CF filings (30 scanned)
*stale-already-done · relevance: none · effort: S · section 2159-2782*

40 vision caches, contributions.csv present, 14 cf_cycle rows ($148,133.14).

### TODO.md:2642 — Herriman (b) [med] — 2021 mayoral PRIMARY existed but is absent from election_results AND the county SOVC dataset
*stale-already-done · relevance: none · effort: S · section 2159-2782*

gov.db election_race has herriman 2021 municipal primary Mayor, 4 candidates, with the note 'Palmer 2,511 / Smith 1,276 / Jared Esselman 1,240 / Nicole Grange 214' sourced from the SLCo election-night report — the exact race and the exact eliminated candidates the entry names.

### TODO.md:2645 — Herriman (c) [med] — structure the CF dollar layer (50 filings acquisition-only; 17 text / 33 scanned)
*stale-already-done · relevance: none · effort: S · section 2159-2782*

herriman_city_council/campaign_finance/filing_totals.csv has 50 data rows (matching the 50 filings), 35 vision caches, contributions.csv present, and 18 cf_cycle rows ($137,229.28). No longer acquisition-only.

### TODO.md:2667 — Murray (c) [med] — 2021 municipal primary existed (Mayor 4, D4 3) per CF filings; races.csv says none
*stale-already-done · relevance: none · effort: S · section 2159-2782*

gov.db election_race has murray 2021 municipal primary Mayor with 4 candidates and a note listing Hales 4,952 / Bullen 2,483 / Fitzgerald 413 / Teemsma 356, plus an explicit finding that the D4 primary was NOT held (Galt withdrew) — which also corrects the entry's own '(D4 3)' assumption.

### TODO.md:2670 — Murray (d) [med] — structure the campaign_finance dollar layer (131 filings acquisition-only)
*stale-already-done · relevance: none · effort: S · section 2159-2782*

murray_city_council/campaign_finance/filing_totals.csv has 130 data rows, contributions.csv present, 63 vision caches, and 46 cf_cycle rows ($327,921.57) — the largest CF cycle count in the wave. No longer acquisition-only.

### TODO.md:2700 — Taylorsville (c)(i) STILL OPEN — 35 filings with no text sidecar and no vision cache (build prints MISSING-TEXT)
*stale-already-done · relevance: none · effort: S · section 2159-2782*

taylorsville_city_council/campaign_finance/ now holds 68 vision/*.json caches against 71 raw PDFs, and filing_totals.csv has 70 data rows for the 71 index rows — i.e. coverage is ~99%, not 36/71. Superseded by the 2026-07-19/20 CF tranches; at most one residual filing remains to confirm.

### TODO.md:2760 — Lehi transcripts rider — 'transcripts feed the federated fts/document layers; cities.db rebuild deferred to a later batched run'
*stale-already-done · relevance: none · effort: S · section 2159-2782*

gov.db document for city='lehi', dataset='transcripts' returns 12 rows (matching the 12 index rows) with has_text=1 and text_path set for exactly the two fetched dates 2026-05-26 and 2026-05-28. The deferred federation ran.

### TODO.md:2866 — CF follow-up (b) — future vision tranches (CH 21, midvale 17, herriman Basham, magna bundles)
*stale-already-done · relevance: none · effort: S · section 2783-3495*

Contradicted by the LARGE+MEDIUM WAVE entry lines 3040-3043 ('CF typed-money tranches all done'), and confirmed on disk: cottonwood_heights vision/ = 58 caches, midvale = 57, magna = 17; gov.db cf_cycle = 805 rows across 29 cities. Only the below-floor sets remain, already tracked at line 2822 — this bullet is a duplicate ledger of a completed task.

### TODO.md:2870 — CF follow-up (c) — shared-lib polish candidates (one pass)
*stale-already-done · relevance: none · effort: S · section 2783-3495*

Each named item verified executed: scripts/campaign_finance/driver.py:18-19 and :393-496 document finance_overrides.csv as WIRED (2026-07-19); scripts/campaign_finance/cycle_totals.py:32/98-110 implements the regime filter and truthful basis labels; the §10-3-208 family promotion was DECLINED on 0/15 ground truth (line 3046); extract_method labels and the loan-substring classifier fix are recorded at lines 3044-3047 and 3276.

### TODO.md:2997 — WAVE-2 (b) — pmn_crosscheck engine hardening (body-text cancel scan, dedup, Rescheduled family)
*stale-already-done · relevance: none · effort: S · section 2783-3495*

scripts/pmn_crosscheck.py:93-95 carries RE_CANCEL = r'cancel|postpone|reschedul' with the comment "'reschedul' added Q3-2026: the 'Meeting Rescheduled' notice family (st_george x5)"; :384 scans the stripped notice DETAIL body; :283 implements the repo_datasets mapping. Also declared closed by the HARDENING BUNDLE at line 3273. Duplicated again as Q3 follow-up (c) at line 3247.

### TODO.md:3011 — WAVE-2 (f) — draper 2 needs_ocr staff reports for the next vision pass
*stale-already-done · relevance: none · effort: S · section 2783-3495*

Contradicted by the LARGE+MEDIUM WAVE entry line 3050: 'both needs_ocr staff reports vision-resolved' in the same 2026-07-19 wave. Bookkeeping residue only.

### TODO.md:3167 — LM wave (p) — batch-guard the 6 dormant reset-pattern classify_attachments.py scripts
*stale-already-done · relevance: none · effort: S · section 2783-3495*

Grepped all six named files: the SCHEMA_SPEC §9 discard-row guard is PRESENT in alta_city_council/packets/classify_attachments.py:159-167, copperton:173-181, kearns:118-127, lehi:142-151, riverton:205-209, and salt_lake_county/packets/classify_attachments.py:114. The mechanical pass this item asks for has already landed; the TODO line was never updated.

### TODO.md:3171 — LM wave (q) — ogden recovery-channel provenance tags (doccenter_draft / packet_carve)
*stale-already-done · relevance: none · effort: S · section 2783-3495*

Read-only SQL against gov.db: SELECT provenance, COUNT(*) FROM motion WHERE city='ogden' returns doccenter_draft=525, packet_carve=34, minutes=1935, pmn_minutes=55 — exactly the design this item proposes, and root CLAUDE.md already documents those two values. Draft-sourced ogden recoveries ARE filterable today.

### TODO.md:3183 — LM wave (s) — slc roster note refresh (Puy's stale 363/361 narrative)
*stale-already-done · relevance: none · effort: S · section 2783-3495*

slc_city_council/roster/council_terms.csv line 14 now reads 'election:2021 (District 2 special - first-choice PLURALITY leader, PUY 1,084 vs Palmer 751; see note)' and the note explains "...363 / Puy 361' ordering was a suppressed-precinct partial-count artifact, FIXED at the elections layer 2026-07-19". The note was refreshed, not left verbatim.

### TODO.md:3195 — LM wave (t) note — 'gov.db election_race is +2 stale for slc until the next federation'
*stale-already-done · relevance: none · effort: S · section 2783-3495*

SELECT COUNT(*) FROM election_race WHERE city='slc' = 59, matching slc_races.csv (60 lines = 59 races + header). The 2026-07-29 federation cleared the staleness. Worth striking the line so a future reader does not distrust election_race.

### TODO.md:3240 — Q3 refresh (b) — harness harmonization (refresh_status probe JSON, herriman fetch_new --probe, CH label match)
*stale-already-done · relevance: none · effort: S · section 2783-3495*

Declared closed by the HARDENING BUNDLE (line 3273-3277: 'Closed the Q3 follow-ups (b)(c)(d)') and corroborated by the LM wave line 3065-3066 ('7 stdout-only cities now emit probe JSON'). Note the residual list at line 3283 still claims 5 stdout-only cities outstanding — the two same-day entries contradict each other. Internal maintenance harness; invisible to researchers either way.

### TODO.md:3247 — Q3 refresh (c) — crosscheck engine hardening (body/description cancel scan, dedup, nephi cross-filing)
*stale-already-done · relevance: none · effort: S · section 2783-3495*

Same verification as line 2997: scripts/pmn_crosscheck.py:93-95, :283, :384 implement all three. This is the THIRD copy of the same task in this range (2997, 3247, and the design-constraint text at 3331).

### TODO.md:3252 — Q3 refresh (d) — referral_overrides.csv unstable-key design (west_valley integer app ids drift)
*stale-already-done · relevance: none · effort: S · section 2783-3495*

west_jordan... checked west_valley_city_council/db/referral_overrides.csv: header is now primary_app_key,related_app_key,action,note and rows key on stable composite strings ('Council|s|minutes/2020/2020-05-04/...|4'), not integer application_ids. The rebuild-drift failure mode this item describes is fixed.

### TODO.md:3256 — Q3 refresh (e) — ordinance backfills owed (slc 22, WJ 8, WVC 5, orem, st_george, park_city 2)
*stale-already-done · relevance: none · effort: S · section 2783-3495*

Read-only SQL: slc has 40 ordinances matching '% of 2026' (1-40 complete, matching the LM-wave claim of 21 added not 22); st_george carries 2026-050..056; park_city 2026-15 and 2026-18 exist as rows with has_text=0 (the documented honest gap — archive unreachable, re-probed in lead (k) line 3112). Residual is only st_george Title 10 codification and an orem re-derivation.

### TODO.md:3261 — Q3 refresh (f) — st_george roster seam (Mayor Hughes + Austin Anderson)
*stale-already-done · relevance: none · effort: S · section 2783-3495*

st_george_city_council/roster/council_terms.csv already models the whole seam at confidence=high: Hughes AL-A1 2024-01-02..2026-01-08 'became-mayor', an explicit VACANT 2026-01-08..2026-01-22 with cited minutes, and Austin Anderson appointed+sworn 2026-01-22 'serving'. The roster update has been run.

### TODO.md:3278 — HARDENING BUNDLE 'STILL DEFERRED' list (basis labels, finance_overrides wiring, §10-3-208, extract_method, stdout-only probes)
*stale-already-done · relevance: none · effort: S · section 2783-3495*

Every one of the five was executed the SAME DAY per the LM wave (line 3044-3047, 3066) and verified on disk: driver.py:18/393 finance_overrides WIRED; cycle_totals.py:32/102 regime-aware with truthful basis labels; §10-3-208 promotion DECLINED on 0/15 ground truth; extract_method labels shipped; 7 stdout-only cities emit probe JSON. Two same-day entries record OPPOSITE states of one list — the clearest bookkeeping defect in this range.

### TODO.md:3476 — [x] Taylorsville campaign-finance vision pass — closure banner vs retained body text ('NOT run yet')
*stale-already-done · relevance: none · effort: S · section 2783-3495*

The [x] banner is CORRECT and the retained body is stale: taylorsville_city_council/campaign_finance/vision/ holds 68 caches, cycle_totals.csv has 8 rows (matching the claimed 15->8 regime-aware reduction), and scripts/campaign_finance/cycle_totals.py:102 reads filing_regime. But lines 3482-3494 still read 'STILL NEEDS VISION ... (13)' and 'NOT run yet', which a future reader will act on. Same failure mode as line 3278.

### TODO.md:3625 — Bluffdale — STILL OPEN follow-up: structure the CF dollar layer
*stale-already-done · relevance: none · effort: S · section 3496-3786*

gov.db shows bluffdale cf_contribution = 410 rows and cf_cycle = 46 rows — the structured campaign-finance layer exists and is federated, contradicting the entry's 'ACQUISITION ONLY, not in cities.db' text. Close with a dated note.

### TODO.md:3658 — Kearns — db/weeks regeneration + cities.db refederation pending (orchestrator)
*stale-already-done · relevance: none · effort: S · section 3496-3786*

/Users/tysonwelsh/civic-data/kearns_city_council/db/civic.db exists (rebuilt 2026-07-20 11:53), the weeks/ directory holds 117 week bundles (2026-07-16), and gov.db has 700 kearns motions federated. The regeneration/refederation happened.

### TODO.md:3710 — Section header: 'New-city-wave rosters — 9 of 14 built; 5 residual'
*stale-already-done · relevance: none · effort: S · section 3496-3786*

The header contradicts its own sub-bullet at TODO.md:3719 ('[✅ DONE 2026-07-13] 5 township→city HB35-seam rosters BUILT + federated ... 31/31 city-town entities'). gov.db confirms: term = 641 rows across 31 distinct cities. The '5 residual' framing is stale bookkeeping that will mislead anyone scanning headers for open work.

### TODO.md:3727 — [med] murray/riverton/midvale precinct layer SKIPPED — add the _precinct_to_district.csv source_year sidecar
*stale-already-done · relevance: none · effort: S · section 3496-3786*

All three now have roster/district_precincts.csv (murray 58 data rows, riverton 40, midvale 43) and gov.db district_precinct carries murray|58, riverton|40, midvale|43. The murray file's note column even records the workaround was applied ('source_year=2023, method=district_contest_precinct_rows'). Done, unchecked.

### TODO.md:3731 — Section framing: 'Votes-pipeline extraction defects flagged by the roster builds' (reworked 2026-07-29)
*not-an-issue · relevance: none · effort: S · section 3496-3786*

Three of four entries are [x] with source-verified closure notes (holladay gibbons = clerk error retained verbatim; alta = body mislabel fixed via body_walk(), 10 body cells changed; emigration bowen = attendance-block over-reach fixed, vote layer MD5-identical). The section's own preamble correctly retracts the 'extraction defects' framing and records the roster_lib.py:437 reword. Only line 3770 remains open. Retitle the header so it stops advertising defects that were disproved.


## Drop (not work: reclassify, delete, or convert to documentation) (25)

### TODO.md:1373 — Phase-5 follow-up — LegiScan account (owner call)
*not-an-issue · relevance: none · effort: S · section 1125-1557*

The public le.utah.gov channel already produced the full 1,208 roll calls / 27,887 named votes with 0 tally mismatches, and the entry itself records LegiScan as a 'documented owner-gated alternative' — it is a standing option, not work, and should live in the GATED section if kept at all.

### TODO.md:1378 — Phase-5 follow-up — mag TAC pre-2020 absent (honest)
*not-an-issue · relevance: none · effort: S · section 1125-1557*

The entry labels it '(honest)' itself — MAG simply did not publish TAC minutes before 2020; this is a recorded source ceiling, not a task, and listing it in a work queue invites a future session to try to 'fix' a non-defect.

### TODO.md:1553 — Watch — run repo-level build_coverage.py after per-city refreshes (2026-07-11 lesson)
*not-an-issue · relevance: none · effort: S · section 1125-1557*

coverage.json (mtime Jul 29 03:00) is newer than every all_votes.csv in the repo and one minute older than gov.db (03:01), i.e. currently true; the lesson is already institutionalized in rebuild_derived.py, so this is a process note that belongs in HANDOFF gotchas, not a work queue.

### TODO.md:1846 — [WATCH — permanent gap] SLC ~8 unrecoverable comment pages (5 content-filter blocks, 3 JSON edge cases)
*not-an-issue · relevance: none · effort: S · section 1558-1920*

Verified documented at slc_city_council/public_comments/CLAUDE.md:45-48 under the heading 'Residual unrecoverable pages (~8, don't keep retrying)' with the 5 API content-filter blocks itemized. The entry tags ITSELF '[WATCH — permanent gap, not debt]' and instructs 'don't burn time on it' — 8 pages against SLC's 13,334 extracted comments is immaterial. This is a documented permanent property of the corpus, not a work item; it belongs in the SLC coverage doc (where it already is), not in the TODO queue.

### TODO.md:2074 — Self-reported INCIDENT: `normalize_motions.py --help` triggered the all-31-city sweep
*not-an-issue · relevance: none · effort: S · section 1921-2158*

TODO.md:2074-2080 records an operational incident that the same note proves harmless (md5 of all 128 non-riverton motions_std.csv identical before/after; only mtimes bumped). It is history, not work, and it is filed inside a completed item's body where it can never be checked off — it belongs in an incidents/journal file, not the future-work queue. (The underlying ergonomics bug — an unknown arg such as `--help` falling through to the bare-run all-city codepath in scripts/normalize_motions.py — is a real footgun if anyone else runs the toolchain post-publication, and would be worth a one-line argparse guard, but it is not tracked anywhere as such.)

### TODO.md:2154 — Notes: murray's 86-video caption-fetch item (now lower priority)
*real-open · relevance: none · effort: L · section 1921-2158*

Confirmed the underlying fact at murray_city_council/CLAUDE.md:171 ('86 videos cover…', captions available, 10 sample VTTs fetched under the owner sample-only policy). This is pure source expansion — no existing query returns a wrong answer because transcripts are missing — and it is already tracked in the repo-wide transcripts/AVAILABILITY program at TODO.md:1858-1868, which enumerates every city's caption situation. Drop this duplicate mention from the Notes bullet and let the transcripts program own it.

### TODO.md:2246 — Park City (c) — Betsy Wallace filed a 2023 primary CF statement but is absent from election_results (withdrew)
*not-an-issue · relevance: none · effort: S · section 2159-2782*

gov.db election_race has a park_city 2023 municipal primary row; the entry itself states Wallace withdrew, which fully explains her absence from results. This is a resolved observation, not work.

### TODO.md:2324 — Vineyard (d) — 2025 general-election candidates filed no finance statements (city gap)
*not-an-issue · relevance: none · effort: S · section 2159-2782*

A statement of an external fact (candidates never filed), with no task attached. Honest gap already recorded; nothing to do.

### TODO.md:2381 — Logan (c) — 2021 winner Ernesto López published no campaign-finance statement (city gap; watch for republication)
*not-an-issue · relevance: none · effort: S · section 2159-2782*

An external non-filing recorded as a watch; no repo defect and no action available.

### TODO.md:2410 — Orem (c) — 2019 + 2021 candidate campaign-finance filings are a confirmed online gap (paper-only at the recorder)
*not-an-issue · relevance: none · effort: S · section 2159-2782*

orem CF index has only 5 rows touching 2019/2021 and the entry records an exhaustive negative search (orem.gov, Wayback, EasyVote, state). Documented honest gap, not work.

### TODO.md:2423 — Ogden CF (c) — 2013 & 2015 combined reports live but out of scope (pre-2019 backfill option)
*not-an-issue · relevance: none · effort: M · section 2159-2782*

Explicitly labelled out-of-scope availability note; pure optional scope expansion below the data floor.

### TODO.md:2454 — Emigration Canyon (d) [low, GENUINE GAP] — 2017 (+ pre-2018-10) minutes/audio/packets purged; MSD AgendaCenter is not a recovery avenue
*not-an-issue · relevance: none · effort: S · section 2159-2782*

Self-labelled GENUINE GAP with the recovery avenue already disproven — this is a documented fact, not an open task, and it is already reflected in the root CLAUDE.md floor language.

### TODO.md:2465 — Copperton (b) [low, GENUINE GAP] — 2017-02→2018-06 (29 meetings) purged; audio purge extends to 2018-11
*not-an-issue · relevance: none · effort: S · section 2159-2782*

Re-confirmed 404 per the entry; the root CLAUDE.md already documents copperton's 2017 floor and the genuine purge gap. A fact, not work.

### TODO.md:2486 — Magna (d) [low, GENUINE GAP] — 2017–mid-2018 minutes/audio/packets blob-purged (same as white_city/kearns)
*not-an-issue · relevance: none · effort: S · section 2159-2782*

Verified-404 external purge, already carried in the root CLAUDE.md magna one-liner ('2017–mid-2018 PMN-purged'). Documentation, not work.

### TODO.md:2500 — Kearns (c) [low, GENUINE GAP] — 2017-01→2018-06 township minutes/audio + 41 pre-2018 PC packets PMN blob-purged
*not-an-issue · relevance: none · effort: S · section 2159-2782*

Self-labelled genuine, all objects 404 with zero Wayback; already reflected in the kearns CLAUDE.md floor note. Not work.

### TODO.md:2517 — White City (b) [low, GENUINE GAP] — 2017 council year (18 meetings) lost to the pre-2019 PMN blob purge
*not-an-issue · relevance: none · effort: S · section 2159-2782*

Notices prove the meetings, minutes 404; entry itself calls it a GRAMA-only lead. Already in the root CLAUDE.md white_city floor note.

### TODO.md:2593 — Midvale NOTE — two agents appended parent-doc sections mid-run against the orchestrator-owns-parent-docs convention (consolidated; reinforce in future prompts)
*not-an-issue · relevance: none · effort: S · section 2159-2782*

A process retrospective whose remedy is already recorded as applied ('done from cottonwood_heights on'). Belongs in an archive/lessons file, not an open-item list.

### TODO.md:2607 — Riverton (d) [low] — 93 within_source ordinance rows (2020–2022) will stay uncorroborated
*not-an-issue · relevance: none · effort: S · section 2159-2782*

The entry states the corroborators do not exist (Riverton's PMN Notice-of-Adoption practice began 2023); the rows are honestly tiered. A fact, not a task.

### TODO.md:2706 — Taylorsville (e) [low] — packets are current-cycle-only; 2020–2026 historical packets unrecoverable (honest gap)
*not-an-issue · relevance: none · effort: S · section 2159-2782*

Self-labelled honest gap with only a 'low-yield, partial' Wayback lead. Documentation, not work.

### TODO.md:2712 — [x] 'Structured campaign-finance layer (NEW, planned 2026-07-05)' — a SECOND closed CF entry duplicating the one at line 2170
*not-an-issue · relevance: none · effort: S · section 2159-2782*

Lines 2170–2232 and 2712–2739 are two [x] entries describing the same CF program, both closed 2026-07-20 as SUPERSEDED; the second is retained 'for the design/history record'. This is archive material duplicated inside the live TODO — move to TODO_ARCHIVE.md.

### TODO.md:3577 — Riverton — 2 dropped roll-call votes from page-header split (2020-05-14 m1 Hartley; 2023-03-09 m2 Breinholt)
*not-an-issue · relevance: none · effort: S · section 3496-3786*

Both allegedly-dropped rows ARE present: /Users/tysonwelsh/civic-data/riverton_city_council/planning_commission/all_votes.csv has 'Kent Hartley,Aye' on 2020-05-14 m1 (7 named rows, matching 'Passed 5-to-2') and 'Keith Breinholt,Aye' on 2023-03-09 m2 (7 named rows, 'Passed 4-to-3'); Hartley appears 65× and Breinholt 181× in that file. The entry also mis-attributes the bug to the COUNCIL extractor — neither date exists in riverton meeting_minutes/all_votes.csv; both are PLANNING COMMISSION meetings. Premise falsified on both counts.

### TODO.md:3586 — Midvale — 1 duplicated roll-call motion (2025-08-19 m1 consent agenda captured twice)
*not-an-issue · relevance: none · effort: S · section 3496-3786*

Programmatic dup scan of /Users/tysonwelsh/civic-data/midvale_city_council/meeting_minutes/all_votes.csv (4,788 rows) finds ZERO duplicate (source,motion_no,member) keys. The 2025-08-19 rows come from two DISTINCT source files ('..._city-council-regular-meeting.md' and '..._city-council-truth-in-taxation.md') — two same-day meetings, not a duplicated roll call. This is explicitly stated 27 lines later at TODO.md:3613 ('was a FALSE ALARM ... no action') — the same fact is recorded twice with opposite verdicts.

### TODO.md:3595 — Holladay — 10 duplicated PC roll-call rows, ALL member 'Layton'
*not-an-issue · relevance: medium · effort: S · section 3496-3786*

Falsified at the primary source. There are TWO Laytons on the 2022 Holladay PC: /Users/tysonwelsh/civic-data/holladay_city_council/planning_commission/minutes/2022/2022-05-16/*.md lines 21/23 list 'Howard Layton, Chair' AND 'Chris Layton' as commissioners, and the roll prints 'Commissioner Chris Layton-Aye ... Chair Howard Layton-Aye' (lines 245-247, 357-359). all_votes.csv now stores them as distinct full names; a dup scan finds 0 duplicate keys. Executing this fix as filed would have DELETED 10 real votes — a cardinal-rule-2 hazard. RESIDUAL WORTH A CAVEAT (not this fix): gov.db still carries a THIRD holladay person, bare 'Layton' (62 votes, 2020-01-07..2022-09-13) alongside 'Chris Layton' (49) and 'Howard Layton' (49) — surname-only source rows that cannot be disambiguated between two serving Laytons, so per-member queries on Holladay PC are ambiguous. Record that as an honest attribution ceiling.

### TODO.md:3679 — Kearns — CRA in-recess body (PMN) not acquired = 0 rows
*real-open · relevance: none · effort: M · section 3496-3786*

Explicitly conditional in its own text ('acquire only if CRA analysis is wanted'). This is scope expansion, not a defect — an unacquired body is an honest absence, not a wrong answer. Reclassify as an acquisition OPTION rather than a task, or delete.

### TODO.md:3690 — Copperton (b) — exhaustively enumerate PC body-1560 notices to close ~80 unsampled dates
*real-open · relevance: low · effort: M · section 3496-3786*

/Users/tysonwelsh/civic-data/copperton_city_council/planning_commission/minutes_index.csv has 17 indexed minutes, matching the filed '18 indexed'. The entry itself records 23/23 sampled dates were cancellation agendas with 'No misses found' — this is a confirmation sweep of a negative, whose expected yield is zero. Not a defect; keep only if someone wants formal completeness proof.


## Section summaries (how each TODO region reads)

### Lines 43-560

Lines 43–560 are essentially ONE entry: a single `- [ ]` [DEBT] container, "NON-CITY-TIER AUDIT FIXES (from _audits/2026-07-25/report.md)", running 502 lines (45–546) with ~20 lettered/tiered sub-items, followed by two `- [x]` items (disposition at 547, T1.3 at 566) that still hide live follow-ups. The ratio is roughly 90% bookkeeping to 10% open work: (a)(b)(c)(d)(e)(f)(g)(h)(h2)(h3)(h4)(i)(j)(l)(m), all of TIER 4, and the provenance half of TIER 5 are closed with dated, unusually well-evidenced notes, and the closures I spot-checked hold up against gov.db and the filesystem (weber 4,404 motions/12,585 votes post-OCR; utah_county 11,218 motions with named divided votes every year 2019–2026; cache 3,388 motions post-dedup; wfrc zero U+202x-contaminated files and zero truncated 'ith ' result_raw; fts_minutes 13,886/40 entities; v_coverage 82 rows). Genuinely open: (e2) 4 missing wfrc motions [low], washington OCR ligature garbling [low], mag_mpo divided-tally loss [medium, and worse than filed — one inverted Pass/Fail and one missing motion], and (j2) died-motion/substitute-roll merges [medium, weber ×4 plus unrecorded ogden ×2 and midvale ×1]. Three items are provably stale-already-done and should just be checked off: (k) coverage.json (now 44 entities, as_of 2026-07-29), TIER 5 raw retention (option b already executed — 25 files/150 MB, documented in cache_county/CLAUDE.md), and the whole TIER-3 "Still open:" list at 399–408. Structurally the section is recorded badly in three specific ways. (1) DUPLICATION: every sub-item keeps its verbatim *(original)* pre-fix text underneath the closure note, so a grep for status words returns fossils — line 361 still says "STILL OPEN (cache)" for a linkage closed twice over, line 355 says "NOT fixed" for a defect closed by (h3) sixteen lines earlier, and lines 399–408 re-open six things marked ✅ in the same paragraph. (2) ITEMS LIVING IN TWO PLACES: the checked `- [x]` disposition entry at 547 carries two live sub-tasks (salt_lake_county disposition; the wrong `recommendation` derivation feeding v_pc_divergence) that no open checkbox surfaces. (3) The section's own closures produced NEW, unrecorded defects of higher publication severity than anything still filed: item (i) seeded caveat rows on 2026-07-25 that the 07-26 repairs falsified, so gov.db still tells every reader that utah_county is "BLIND to every divided Board vote after 2018" and that weber has 21 scans "never OCR'd"; and TIER 4's "BATCH CLEARED" left root CLAUDE.md:356–363 warning researchers off utah_county's now-repaired vote layer. Those two — both S-sized text fixes plus a re-federation run — are the only publication blockers in the range, and neither is written down anywhere as work.

### Lines 995-1124

TODO.md lines 995-1124 is the tail of the big deferred-work block: one [OPTION] state-tier redesign, two [NEW 2026-07-29] [DEBT] clusters spun out of the ordinance-link and Tier-1-fabrication passes (5 lettered sub-items total), one [DEBT] acquisition gap (Riverton Timberline), and one [OPTION] scope-control register. Genuinely open work vs bookkeeping runs roughly 60/40: of 8 triage rows, 5 are verified real-open defects, 2 are partially-done entries whose closure notes are inaccurate, and 1 (the watch list) is not work at all. Nothing here is a publication blocker; only two items meet the wrong-answer test — (1) the midvale date-collision cluster at line 1057, which I verified is UNDERSTATED (a fourth midvale pair in the planning_commission dataset, plus previously-unrecorded instances in magna PC, weber_county 2021-06-01, and holladay 2025-05-01, ~20+ motions filed under wrong dates across 4 entities), and (2) the doc-figure half of line 1083, where root CLAUDE.md:162-166 now quotes county counts (27,376/39,237/77,507) that are exactly 107 motions / 640 votes above the shipped gov.db (27,269/38,597/77,400) because the cache_county h3 de-dup at TODO.md:327 was never propagated into the headline numbers. Structural problems with how the section is recorded: (a) the SAME stale count triple appears in three places — CLAUDE.md:162-166, TODO.md:420 (the (j) closure) and TODO.md:1086 — with HANDOFF.md:110,157 staler still, so one number lives in four documents and none of them agree with the database; (b) two entries assert work that only half-landed (line 1083's CLAUDE.md update, line 1109's fetch_status=error:auth_wall relabel, which grep shows never touched index.csv despite AVAILABILITY.md:97 claiming it) — a pattern of closure notes written from intent rather than from re-reading the artifact; (c) line 1057's defect is filed as a midvale-specific extraction bug when it is really a repo-wide class (mis-dated duplicate meetings from filename parsing, approval-date-as-meeting-date, and PMN re-posting), and the entry itself half-recognises this by asking for a date-collision detector — that detector, not the three named midvale rows, is the actual deliverable; (d) the Riverton item is duplicated in substance with the residual note inside the closed vision-pass entry above it (lines 992-997), so the same gap is tracked in two places.

### Lines 1125-1557

TODO.md lines 1125-1557 are the "[OPTION] Multi-level entity tier" section — the narrative record of how the repo went from 16 cities to 44 entities across four tiers (Phases 2-6, 2026-07-11 → 07-22), plus the surviving residual queues. Structurally it is ~85% BOOKKEEPING and ~15% open work, but the bookkeeping is load-bearing history (the Phase-4/5/6 [x] blocks are the only record of what was built and why), so it should be archived rather than deleted — ideally moved to a CHANGELOG/BUILD_HISTORY doc so TODO.md stops reading as a 400-line wall of completed work with open items buried inside it.

Genuinely open work falls into four groups: (a) the WFRC-NATIVE package Phases 2-5 (line 1434) and the 10-item County content menu (1519-1549), both pure capability expansion on entities that already ship — together they are the biggest refinement-creep magnet in the file and belong behind a "post-publication" wall; (b) named acquisition residuals from Phases 4-5 (items A-F at 1281-1310 and the Phase-5 list at 1371-1378), nearly all of which are honestly ledgered in the affected minutes_index.csv files and therefore surface to a researcher as visible gaps, not wrong answers; (c) a handful of genuine correctness items; (d) several entries that are already done or were never defects.

Four findings worth acting on before publishing. (1) **Disposition coverage is silently inconsistent across the non-city tier** (line 1304): cache_county (2,949 motions) and mag_mpo (577) ARE classified while salt_lake_county, summit_county, utah_county, weber_county, wfrc_mpo and ut_state are all zero, with no caveat row covering it — the documented `disposition='deny'` idiom returns cache-only results across counties, and root CLAUDE.md's blanket "County motions have NULL disposition" is now false. (2) **The logan "North Logan RCV" claim is confirmed WRONG** (line 1300) — cache_county/elections/CLAUDE.md:41-45 proves North Logan never used RCV, while logan_city_council/election_results/CLAUDE.md:11,183 and recon.md:235 still tell readers it did; a one-edit fix. (3) **v_pc_divergence and the whole referral layer are city-only** (line 1432) — zero county rows, so a flagship documented query silently returns nothing for the county tier. (4) **No cross-tier analytical view exists** (line 1547) — the four-tier model's headline promise has no shipped query surface.

Three items should be closed or dropped outright: the /build-county-data-repo skill lesson absorption (1513) is fully landed in SKILL.md lines 119-124, 143-144 and 241; the county projections menu item (1539) was delivered by Phase 4 (980 county rows in gov.db); and the Phase 3 [~] marker (1219) plus the Phase 2 election-repoint follow-up (1157) are both satisfied, with Phase 3's sole survivor already double-tracked at 1492 and 1519.

Two structural defects in how this section is recorded. First, **duplicate tracking**: the county content menu is stated three times (the Phase-3 "NEXT", the residual item at 1492, and the menu block at 1519), and the disposition gap appears both here at 1304 and in the Phase-6 residuals at 1432 — a future session could work either copy and leave the other looking open. Second, **stale absolute counts inside [x] closure notes**: the Phase-4 (1250) and Phase-6 (1426) blocks quote county motions 24,346 / regional 958, while live gov.db reports 27,269 / 959 — and neither matches the 27,376 that TODO.md:1086 and root CLAUDE.md both claim after the 2026-07-29 re-federation, meaning a later rebuild moved the number again unrecorded. Any publication doc numbers must be re-derived from live SQL, never copied from these notes. Related cross-reference outside my range: TODO.md:129-130 records the utah_county vote-layer repair as DONE (gov.db confirms 11,218 motions), yet root CLAUDE.md still carries the ⚠ "do not read its post-2018 contested rate as real" warning — that stale warning is a publication blocker in its own right and is owned by the audit-fixes section, not this one.

### Lines 1558-1920

Lines 1558-1920 cover three adjacent buckets: [GATED] (one owner-deferred item), [WATCH] known acquisition gaps, and the first half of [DEBT] extraction/data-quality follow-ups. It is overwhelmingly BOOKKEEPING, not work: of ~24 discrete entries in the range, 14 are fully [x] with long verified closure notes, and of the 12 open-looking rows I triaged only 6 are genuinely open work — Wayback archiving (owner-gated, low value), 4 watch/monitor items that are externally blocked and already ledgered in minutes_unrecovered.csv or a city CLAUDE.md, the provo+ogden halves of the roster boundary item, the referral-guard rollout beyond ogden, and the XL spoken-comment transcript OPTION. NOTHING in this range is a publication blocker: every gap it describes is already disclosed at the exact place a researcher would land (minutes_unrecovered.csv rows with md5 forensics, confidence=low geometry notes, geo/CLAUDE.md 'PRECINCT-DERIVED, not official' headings), which is this repo's stated cardinal rule working as designed. Structural problems with how it is recorded, all worth a cleanup pass before publish: (1) STALE ENTRIES THAT READ AS OPEN — the Alta 2025 election item (1709) was refuted and superseded on 2026-07-17 (the election was CANCELLED under Utah Code 20A-1-206, so the prescribed 'refetch the SOVC' action is impossible), and the 'federated Ogden referral rows remain stale' warning (1798) is disproved by gov.db (6 rows, identical to ogden's local db). (2) SELF-CONTRADICTING ENTRIES — the full-name voter-resolution item (1744) is headed COMPLETE yet still carries a 'STILL TODO (a)(b)(c)' paragraph whose three tasks I verified landed in code; the election-URL item (1620) nests a 'NOT DONE (deferred, minor)' block that its own next paragraph closes. (3) DUPLICATION ACROSS SECTIONS — the Alta 2025 election is tracked twice (1709 and 2432(b)), both stale. (4) STALE SCALE FIGURES inside otherwise-valid items — Wayback says '~6,700 URLs' where the repo now holds 46,522 distinct source URLs (7x), and the roster boundary item says '5 of 9 done' where disk shows 7 of 9. (5) MISCLASSIFICATION — the SLC 8-page comment gap and the Taylorsville geo item are permanent externally-blocked properties filed under DEBT/work rather than as documented coverage facts. Recommended action before shipping: close/delete 6 rows, correct 2 counts, and let the remaining 6 ride as backlog.

### Lines 1921-2158

Lines 1921-2158 are the "[DEBT]+[WATCH] Minutes-promotion wave — COMPLETED 2026-07-16 (13 cities); new follow-ups" section: a narrative header recording a finished repo-wide promotion, then 12 lettered follow-ups the wave surfaced, then an un-checkboxed "Notes:" bullet. It is overwhelmingly bookkeeping — 10 of the 12 follow-ups are [x] with long forensic closure write-ups (riverton's extractor recoveries alone run ~60 lines), and I verified two of those closures independently (the rec-not-ceremonial fix is live in gov.db with exactly 62 `rule:rec-not-ceremonial` rows; the CH federation rider is satisfied — db 1468/1430 == disk 1468/1430). Only 2 top-level items are open, and both are low-stakes: the herriman Appeal Authority body (2 docs, already disclosed in herriman's CLAUDE.md) and a Watches list of external portal re-checks, all four of which are already honestly ledgered in minutes_unrecovered.csv / pmn_backfill indexes. Roughly 85-90% history, ~10% genuinely open, and NOTHING in the section as written is a publication blocker.

Structurally the section is recorded badly in four ways. (1) Completed items carry buried NOT-DONE riders that are tracked nowhere else — the "cities.db now stale for CH" note (2098-2100, since satisfied) and the deferred land-use-rule enhancement (1982-1985, still open) both sit inside [x] bodies where they can never be checked off. (2) The trailing "Notes:" bullet (2153-2157) carries four real follow-ups with no checkbox at all, so they are permanently unclosable. (3) Several items live in two places: murray's caption fetch duplicates the transcripts/AVAILABILITY program at 1858-1868, and the appeal-authority modeling duplicates the Orem BoA / hearing-officer class at 2407 and 3320. (4) A self-reported operational incident (2074-2080), proven harmless, is filed in the work queue instead of a journal. The header's statistics are also superseded — it reports 2,189 recovered-provenance motions, while gov.db today has 4,538 (2,932 city-tier) — harmless as history but it means the section cannot be read as current state.

The most important thing in this range is NOT one of its listed items: two claims made in passing by the header turned out to be wrong when checked. "Search-layer reconciliation exact" (line 1928) hides that all 935 text-bearing `pmn_minutes` documents are excluded from `fts_minutes` by a doc_type filter at scripts/build_search_layer.py:642-644, so the advertised thematic-keyword workflow silently misses entire recovered eras (herriman 67/67 recovered source files absent, midvale 24/24, magna 16/16, alta 4/4, provo 391 docs) while CLAUDE.md and cities_db_SCHEMA.md:128 both promise full minutes coverage — that is the one fix-before-publish item here. And the accepted "Meetings: 0 is just the promoted-doc convention" note (1932-1933) is wrong for two-thirds of the affected bundles: 206 weeks summaries repo-wide show Meetings:0 with votes>0, and bluffdale's 136 are caused instead by scripts/weeks_lib.py:91-93 deriving meeting dates from `f.stem[:10]` when bluffdale is the only city with non-date-prefixed minutes filenames (166/166), so every bluffdale weeks bundle reports zero meetings and links no minutes.

### Lines 2159-2782

TODO.md lines 2159–2782 are the "[TAIL] Expansion & routine operations" section, whose own header says these items "fold into the quarterly refresh, do NOT queue." Structurally it is ~20 per-city umbrella entries (one per city that received an `expand-city-sources` run, 2026-07-05 through 2026-07-14), each holding 3–6 lettered sub-tasks, plus two closed campaign-finance program entries, one [OPTION], and four closed operational entries. Every umbrella is still an unticked "- [ ]" even where every substantive letter inside it is ✅ DONE — the checkbox state of this section is essentially meaningless.

Ratio of genuine open work to bookkeeping: LOW. Of ~95 sub-items I triaged, only two are worth acting on before/near publication: **Draper's campaign-finance layer is unstructured** (line 2620 — draper/campaign_finance/ has only index.csv + raw/, and draper is absent from gov.db `cf_cycle`, which covers 29 of 31 cities; SLC at line 2164 is the other absentee, portal-blocked) and **South Salt Lake's 2021 mayoral primary is still missing from election_race** (line 2540). One cheap correctness win sits at line 2420: Ogden's `election_race` has ZERO primary rows across 2019–2025 while ten other cities carry primaries — ogden/election_results/CLAUDE.md says "Primaries not output — per the task" and the raw primary PDFs are already on disk, so the asymmetry is fixable in an hour and is disclosed nowhere in the federated docs.

Everything else falls into four piles. (1) **Stale-already-done but never ticked — 19 items.** I verified each against the repo: Alta's 2025 general (present in alta_races.csv as a cancelled certification, so the entry's proposed SOVC re-pull was also methodologically wrong), Emigration Canyon's 2019 cycle AND the Griffith appointed-not-elected roster fix, Copperton's 2019 A/B/C cycle, Magna's 2023 + 2016/2019 D1/D3/D5 "double gap", Holladay's 2019 D2/D4/D5, Cottonwood Heights' 2019 D1 primary (the db note explicitly cites the 2026-07-16 re-parse and McHugh's 189 votes), Herriman's and Murray's 2021 primaries, Midvale's fts_ordinance load (263 rows, exactly as claimed), the polite_fetch.py comma bug (fixed; pre-fix copy in _backups/2026-07-16-minutes-promotion/), Emigration Canyon's "empty core scaffolds" (db/geo/elections/public_comments all exist), and eight per-city "cf-vision-transcribe the N filings" letters superseded wholesale by the CF-structuring package closed at line 2170. (2) **Facts mislabelled as tasks — ~12 items**, all self-tagged "[GENUINE GAP]" or "city gap" (2017 PMN blob purges, candidates who never filed, paper-only recorder archives). These are documentation and belong in AVAILABILITY/COVERAGE files, not an open-work list. (3) **Standing quarterly-refresh routines** (re-crawl ordinance portals, re-probe codification lag, watch for unposted CF cycles) — exactly what the header says to fold in. (4) **Whisper/transcript and packet-mirror scope expansion** — every one an explicit "proposed only" or "[OPTION]", and the owner has already ruled transcripts SAMPLE-ONLY (line 2743).

Structural problems worth fixing before publishing the repo: (i) the section mixes an executed-and-archived program record with live work — lines 2170–2232 and 2712–2739 are two separate [x] entries for the SAME campaign-finance program, and lines 2161, 2747, 2763, 2771, 2777 are closed entries retained inline; all of it belongs in TODO_ARCHIVE.md, which the repo already has. (ii) Four entries carry "cities.db needs a build_cities_db.py run (not run here)" riders (lines 2271, 2287, 2320, 2760) — I verified ALL FOUR are now satisfied in gov.db (nephi 989 motions on disk = 989 federated; vineyard Ord 2021-12 → 2021-09-08 #4 at `high`; lehi transcripts 12 document rows with has_text on the 2 fetched), so those riders are pure noise that makes the federation look staler than it is. (iii) Several leads are duplicated across sections (Copperton's seat-lettering owner question is also an LM-wave item; Draper's canceled-race note also lives in the roster H-C/H-E item). (iv) A real cross-cutting documentation gap this section exposes: `gov.db`'s `caveat` table has NO rows for any finance dataset (`SELECT * FROM caveat WHERE dataset LIKE '%finance%'` returns nothing) and cities_db_SCHEMA.md never states which cities `cf_*` covers — so the Draper/SLC absence and the Kearns blocked-cycle incompleteness are invisible to anyone querying the db. Adding two caveat rows would be a far cheaper publication safeguard than doing the underlying work.

### Lines 2783-3495

Lines 2783-3495 are the repo's late-July-2026 EXECUTION LEDGER plus the [GATED] Infrastructure section. Structurally it is ~85% bookkeeping: six huge dated wave records (RECOVERY+EXTRACTION+CF 2026-07-17, WAVE-2, LARGE+MEDIUM 2026-07-19, Q3 QUARTERLY REFRESH, HARDENING BUNDLE, CF-STRUCTURING PACKAGE) that are all [x] but each carry 5-22 lettered follow-ups, many of which were executed the SAME DAY by a later wave in the same file and never re-marked. Of the 39 rows I filed, 15 verified stale-already-done and 1 verified not-an-issue — i.e. roughly 40% of what reads as open work in this range is already done or rests on a false premise. Genuinely open and worth doing: the two [GATED] Infrastructure items (git init + GitHub publish), the two CF owner questions at line 2859, the murray 2021 primary election flag (line 2881), the SSL published-vs-unposted work-meeting distinction (line 3263), and the unfinished half of re-pointing 7 city election pipelines at the county canonical (line 3200). Everything else is external acquisition (GRAMA, auth-walled portals, an unpublished county GIS snapshot), owner-gated scope expansion (Whisper audio, orem RDA promotion), or monitoring cadence.\n\nThree structural defects in how this section is recorded. (1) SAME-DAY CONTRADICTIONS: the HARDENING BUNDLE's 'STILL DEFERRED' list (line 3278) names five items the LARGE+MEDIUM entry 200 lines above records as executed on the same date, and I verified all five landed in code; the taylorsville CF item (line 3476) carries a DONE banner over a retained body that still says 'NOT run yet'. A reader working top-down will redo finished work. (2) TRIPLICATION: the pmn_crosscheck engine hardening appears as WAVE-2 (b) at 2997, Q3 (c) at 3247, and design-constraint text at 3331; the CH Prazen and riverton Pierucci acquisitions appear at both 2878 and 3007/3009; the CF owner questions appear at both 2859 and inside the [GATED] hand-check at 2918/2930. (3) CLOSED INVENTORIES PRINTED AS OPEN: the [~] PMN-crosscheck entry (3284) states in its own header that both recovery tiers are worked to zero, then prints both tier inventories as live bullet lists for 18 lines.\n\nThe single most consequential finding for the owner's publish goal is not in the TODO text at all: the pre-worked .gitignore ignores '/cities.db', which the 2026-07-20 rename turned into a 6-byte symlink, while the actual 1.6 GB gov.db at repo root is unignored — so the first `git add -A` stages a file 16x over GitHub's 100 MB hard block, alongside a second >100 MB offender (a draper packet text file at 110 MB). The real tracked footprint measures 2.04 GB / 59,978 files, not the '~800 MB' both Infrastructure entries assume. There is also no LICENSE file, which matters for a corpus meant to be cited by outside researchers. All three are S-effort and should be settled before the first push. (Tangential observation while querying: gov.db cf_cycle stores bluffdale's Natalie Hall as 'Natalie Hall' for 2021 and 'NATALIE HALL' for 2025 — candidate-name casing is not normalized in that table, which will bite anyone grouping donors by candidate across cycles.)

### Lines 3496-3786

TODO.md lines 3496-3786 (end of file) is the TAIL of the per-city follow-up log from the 2026-07-06 three-city wave, the 2026-07-12/13 Salt-Lake-County 15-city wave, and the 2026-07-29 rework of the roster-flagged vote items. It is roughly 70% bookkeeping/history and 30% genuinely open work, and almost all of the open work is S-effort polish. Of ~20 items I triaged: 5 verified STALE-ALREADY-DONE (bluffdale CF dollar layer — 410 cf_contribution + 46 cf_cycle rows in gov.db; kearns db/weeks/refederation — civic.db rebuilt 2026-07-20 and 700 motions federated; murray/riverton/midvale precinct sidecar — district_precincts.csv built and federated 58/40/43; the '5 residual rosters' header — term=641 across 31/31 cities; the votes-pipeline defects section), 4 verified NOT-AN-ISSUE and recommended for deletion, and ~10 real-open but low-stakes. Exactly ONE item materially affects a published query surface: line 3770, the Draper 2025 canceled-uncontested 4-year Council race, confirmed absent from draper_races.csv (only 3 2025 rows exist) — two sitting councilmembers have no election record. Next-most-real is line 3612 (midvale 'Erikson' vs 'Erickson' = two gov.db person rows for one commissioner, splitting 13 of 280 votes). STRUCTURAL PROBLEMS WITH HOW THIS RANGE IS RECORDED: (1) The three 'duplicated/dropped roll-call' sections at 3577 (Riverton), 3586 (Midvale) and 3595 (Holladay) are ALL falsified at source — riverton's two 'dropped' votes are present (and are PC, not council, meetings as filed); midvale's 'duplicate' is two distinct same-day meetings; and holladay's '10 duplicate Layton rows' are TWO REAL PEOPLE, Chair Howard Layton and Commissioner Chris Layton, both printed in the 2022-05-16 minutes. Executing the holladay fix as written would have DELETED 10 genuine votes — the same cardinal-rule-2 hazard the 2026-07-29 rework warned about ('a name outside its tenure window is a QUESTION, not a diagnosis', 3742), which was applied to that section but never back-applied to these three. (2) The same fact is recorded twice with OPPOSITE verdicts: 3586 files the Midvale dupe as a defect and 3613 (27 lines later, in a different section) calls it 'a FALSE ALARM ... no action'. (3) Closure notes are written INSIDE the [x] title text, so residual open work is invisible to a checkbox scan — the phrases 'STILL OPEN follow-up' (3625), 'Remaining minor' (3611) and 'Untouched 2026-07-29' (3773) are buried in DONE entries; in this range MORE open work lives inside [x] items than in unchecked boxes. (4) Section headers go stale independently of their sub-bullets (3710 '5 residual' vs its own '✅ DONE ... 31/31' child; 3731 'extraction defects' vs its own retraction). One NEW finding not in any entry: gov.db still carries a bare-surname holladay person 'Layton' (62 votes, 2020-01..2022-09) alongside 'Chris Layton' (49) and 'Howard Layton' (49) — surname-only source rows that cannot be disambiguated between two serving Laytons; that deserves a caveat row, not a fix.

