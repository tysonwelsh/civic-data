# TODO — the work queue (restructured 2026-07-31)

**This file holds ONLY terminating work: [DEBT] (wrong or missing values, evidence-cited) and
[GATED] (owner decisions), plus the active PUBLISH GATE package. The open-box count here IS a
true measure of work owed.** Everything else lives elsewhere:

- **`LEADS.md`** — options, expansion menus, acquisition leads, and the WATCHES table. A menu,
  not a queue; no checkboxes; not doing an item there is never a defect.
- **`TODO_ARCHIVE.md`** — every closed record, verbatim, under dated anchors. The full
  pre-restructure TODO/HANDOFF/NEXT_SESSION_PLAN are archived under
  `ARCHIVE ANCHOR 2026-07-31-RESTRUCTURE`.
- **`SHIP_GATE.md`** — the three runnable state predicates that define "ready to publish."
- **`GOTCHAS.md`** — standing operational rules (moved out of HANDOFF.md).
- **`_audits/2026-07-31-publication-review/`** — the 13-agent review that produced this
  restructure: `report.md` (synthesis) + `triage_full.md` (all 245 verified rows; its TODO.md
  line references resolve against the archived snapshot).

**Rules (also in CLAUDE.md):** a backlog entry is EVIDENCE, NOT FACT — verify at the primary
source before working it (the 2026-07-31 triage falsified three filed defect sections, incl.
holladay's "10 duplicate Layton rows" = two real people; executing it as filed would have
deleted 10 genuine votes). New items enter here only as [DEBT] with a primary-source citation
stating what was OBSERVED, or as [GATED] by the owner. Leads go to LEADS.md, never here. No
umbrella items — one box, one terminating task. Closing an item moves its record to
TODO_ARCHIVE.md in the same session, leaving one changelog line here. A closure that falsifies
a claim in CLAUDE.md/README updates that claim in the same session.

**Definition of done is a STATE, not an empty list** — see SHIP_GATE.md. Open [DEBT] blocks
publish only if it makes a published value WRONG; incompleteness ships with its caveat.

---

## PUBLISH GATE — active work package (owner-approved 2026-07-31)

Ordered. Full detail per item: `_audits/2026-07-31-publication-review/report.md` §2.

- [x] **G1. git init + private remote — ✅ DONE 2026-07-31.** .gitignore corrected
  (`/gov.db` + `/cities.db` symlink + the 110 MB draper whitespace-bloat sidecar
  [re-extraction lead in LEADS.md] + `mag_mpo/legislative/raw_pdf/` [name kept — referenced
  by its index/provenance] + `*/pmn_backfill/work/`, `_backup_*/`, `*.bak`,
  `.claude/settings.local.json`); every rule check-ignore-verified incl. both `.env` files;
  oversize scan clean (largest staged file 42.7 MB); 59,468 files / 548 MiB committed
  (`e9872b9`) and pushed → **private `github.com/tysonwelsh/civic-data`** (main). OWNER
  RESIDUE: rotate the ANTHROPIC_API_KEY (cheap insurance); enable secret scanning + push
  protection when the repo flips public (free tier is public-only).
- [x] **G2. Caveat refresh + re-federation — ✅ DONE 2026-07-31.** Caveat table 63→88 rows:
  falsified utah_county/weber rows rewritten (post-repair reality + the 42-of-63 honest
  residual); south_jordan PC `dissent-only` row added (Hollist's 100% nay rate now caveated);
  millcreek comments caveat rewritten to the built-harvest state (+ sliver enumeration);
  16 zero-caveat entities back-filled from their documented ceilings; disposition-coverage +
  cf-coverage/cf-honest-zero(slc)/cf-unstructured(draper)/cf-blocked-cycles(kearns) added;
  summit disposition caveat reworded. Federated (built 2026-07-31T14:30:48, integrity ok,
  FK 0, reconciliation exact) + `--federation` 44/44 in step; 0 built entities uncaveated.
- [x] **G3. LICENSE/CITATION/METHODS/PRIVACY — ✅ DONE 2026-07-31 (owner decisions:
  MIT code / CC-BY-4.0 data / strip comment emails+phones / ship CF text verbatim).**
  Shipped: LICENSE (MIT) + DATA-LICENSE.md (CC-BY-4.0 with public-records + third-party
  carve-outs) + CITATION.cff (type: dataset, v2026-07-31) + METHODS.md (per-layer
  extraction table incl. the LLM/Vision disclosures + audit regime) + PRIVACY.md (verbatim
  docs as published; constructed comment layers contact-redacted; takedown contact) +
  README "License & citation" section. Redaction executed: `scripts/redact_comments.py`
  (new, idempotent) removed 635 emails + 248 phones across 87 files (canonical CSVs + slc
  JSON + weeks copies); re-run rule added to GOTCHAS.md; builder-integration lead in
  LEADS.md. NOTE: gov.db's comment/fts_comment pick up the redacted text at the next
  federation (G5/G8 rebuild — before any G9 release asset is cut). Zenodo DOI mints at G9.
- [x] **G4. Doc-consistency pass — ✅ DONE 2026-07-31.** README (headline table
  27,269/38,597/959, projections row realigned, 44/41 entity split, utah_county bullet,
  comments 6-sliver/23-zero recount, CF 29-of-31, validate_entity side-effect note);
  CLAUDE.md (headline counts, entity split, disposition per-entity, provenance two-
  vocabulary rewrite with the tier-safe filter, utah_county bullet rewritten post-repair,
  roster line → all 31, riverton 555, nephi ~51, ut_state fts 519); schema doc REGENERATED
  as `gov_db_SCHEMA.md` from the live db (all 34 tables incl. the 6 previously-missing,
  path-prefix rule, corrected example queries — docs-not-mentions, donor_type 3.5% scope
  note; `cities_db_SCHEMA.md` is now a pointer stub); false "Elections are not in
  cities.db" caveat text + nephi ~58 fixed at source in build_cities_db.py (lands at next
  federation); 5 closed planning docs → `docs/history/` (3 live references re-pointed);
  sources_summary/refresh_status SNAPSHOT-bannered. Permanent gate:
  **`scripts/check_doc_numbers.py`** (new) asserts 13 headline-number checks
  docs-vs-gov.db — all PASS; wired into SHIP_GATE.md predicate 3.
- [x] **G5. Search-layer fixes — ✅ DONE 2026-07-31.** `pmn_minutes` texts now indexed via
  their `text_path` (823 indexed; 112 skipped as same-(city,date,body) duplicates of
  promoted minutes — rule documented in gov_db_SCHEMA.md); statutes get a 40-char floor
  (+4 LUDMA sections; sub-floor skips print as honest gaps). fts_minutes 13,886→**14,713**
  (ut_state 519→523; only image-only AOs #142/#145 remain unindexed). Re-federated; the
  build also picked up the G3 comment redaction (141 redacted rows live in `comment`) and
  the G4 caveat-text corrections. check_doc_numbers named the 3 moved doc lines; all
  reconciled, 13/13 PASS.
- [x] **G6. Consumer packaging — ✅ DONE 2026-07-31 (release asset itself deferred to G9
  so it isn't cut stale before G8's data fixes).** README QUICKSTART shipped (3 commands,
  mode=ro idiom, FTS5 note); `examples/marquee_queries.py` (5 marquee questions, doubles
  as doc regression test — all return results); `DATA_DICTIONARY.md` generated from
  PRAGMA via new `scripts/build_data_dictionary.py` (35 tables + column glosses);
  `gov-sample.db` (21.3 MB, vineyard + wfrc_mpo slice via new
  `scripts/build_sample_db.py` — both tiers demonstrable, fts_minutes included);
  `build_status` column added to registry/entities.csv (39 built / 2 built_dbless / 3
  registered_only; hierarchy regenerated; 2 stale registry notes fixed — utah_county's
  retracted framing, SSL's pre-recovery note). Path-prefix + document.path rules were
  documented in gov_db_SCHEMA.md at G4.
- [x] **G7. Build hardening — ✅ DONE 2026-07-31, proven on a live run.** build_cities_db.py
  now: takes an exclusive `gov.db.lock` (refuses concurrent federations — the GOTCHAS rule
  enforced in code), builds into `gov.db.tmp` and `os.replace()`s onto gov.db only after
  the integrity gate passes (mid-build crash leaves the prior db intact), and auto-runs
  `validate_entity.py --federation` at the end of every build (printed 44/44 in step on
  the 15:58 run; nonzero exit propagates). Both temp paths gitignored since G1.
- [x] **G8. Wrong-value data fixes — ✅ DONE 2026-07-31.**
  (a) **mag_mpo**: RESULT_RE grammar fixed (optional "The", sentence-end tallies, bare-"move"
  typo) → 635→649 motions (+14, zero lost, motion-level diff proven), Fail 3→5, the
  2015-11-05 failed strike + its 12 named dissenters recovered verbatim; CLAUDE.md + caveat
  corrected (dissent IS sometimes named in result_raw); named-dissent parsing → LEADS.
  (b) **Date-collision class — 17 pairs verified, not the filed ~5**: new
  `scripts/detect_date_collisions.py` (213 raw pairs → body-text diffing → 17 confirmed
  duplicates across 10 entities, incl. nephi/vineyard/CH/summit/WVC/slco/herriman the TODO
  never knew). Owner-approved 10-agent Opus wave fixed all of them (backups, source
  adjudication, exact-delta proofs, per-entity validators green): ~70 phantom motions +
  ~190 phantom vote rows removed; ~10 vacated REAL meetings honestly ledgered (LEADS
  recovery class); midvale's Revize date parser + weber's mis-post guard root-fixed; magna's
  agent found+fixed an unassigned 4th pair; 2 pairs proven both-real and untouched (weber
  clerk copy-paste documented). Detector re-run: class CLOSED.
  (c) **weber 2019-07-30 Solar Overlay**: filed cause WRONG again — the real bug was a
  generic roll-scan loop-skip (`i=j+1` stepping over the next motion) that had eaten
  **15 motions corpus-wide**; all recovered (+31 votes, incl. a 2-1 contested resolution);
  Ord 2019-13 now uniquely linked with its full named roll.
  Closed with ONE federation (build 2026-07-31T17:00:54): auto-gate 44/44, integrity ok,
  reconciliation exact; docs reconciled (check_doc_numbers 13/13); coverage.json + sample db
  + data dictionary regenerated; marquee examples 5/5.
- [x] **G9. Declared + PUBLISHED 2026-09-02 (owner-directed).** All three SHIP_GATE
  predicates re-run PASS on commit `059b332cf`; repo flipped PUBLIC
  (github.com/tysonwelsh/civic-data) with secret scanning + push protection enabled;
  release **v2026-09-02** cut with gov.db.gz (407 MB, sha256 sidecar); the 3 open [DEBT]
  items became issues #1–#3 (leads stayed in LEADS.md; honest ceilings became nothing).
  OWNER RESIDUE: mint the Zenodo DOI (CITATION.cff ready; wire DOI into README/CITATION
  when minted), link from municipalsky.com, rotate the ANTHROPIC_API_KEY.

## COUNTY DATA ACQUISITION — active work package (owner-authorized 2026-08-01)

Spec + technical pointers: HANDOFF.md. Owner-authorized in response to live query tests
(the "largest county-race donor" question was unanswerable twice over).

- [x] **A. SLCo county-office election results — ✅ DONE 2026-08-01.** 61 raws mirrored
  in-repo (29 SOVC workbooks + 31 certification PDFs + 1 CVR, sha256'd in sources.csv);
  normalizer families ported + THREE never-parsed eras cracked (2002/04 family G, 2006
  family E, 2020 SpreadsheetML); every even-year workbook 2002–2026 parsed under dual
  hard gates (internal certified-total: 3,624 exact / 185 suppression-deficit / 2
  verbatim source contradictions allowlisted; external certification-PDF: 115/115).
  Federated: election_race 688→**810** (+122 audited county races, 2 AUDIT-FLAG rows),
  election_result 5,482→**5,820** (+338 rows w/ new election_date/certified_votes/
  votes_basis columns); 4 caveat rows. Rider CLOSED: washington's 2018 floor claim was
  CORRECT (tier mix-up — docs reworded). Follow-on (other counties' election_race
  promotion) + 56 below-city-floor municipal contests → LEADS.md.
- [x] **B. County-candidate campaign finance — ✅ DONE 2026-08-01, 8 counties (wasatch
  included by owner).** ~2,270 county-office filings landed: salt_lake 989 (EasyVote
  2024/2026 STRUCTURED — 4,956 contributions/$1.9M + 3,278 expenditures/$1.6M; API
  recipe documented), washington 402 (2006–2025, deepest), utah 267 (2008–2026, Strapi
  channel find), cache 249, summit 131 (every ballot candidate covered), wasatch 111,
  weber 98 (+33 county-lost interims citably ledgered), juab 27 (recon false-negative
  REVERSED — the residence-town folder trap). `load_cf` extended CITIES→all entities
  (city rows proven byte-identical excl. the st_george DEBT fix); cf-coverage caveat
  rewritten + 8 per-county ceiling rows. Vision/structured pass + GRAMA asks + shared
  family specs → LEADS.md (owner scope decisions).

## [DEBT] — correctness queue

- [ ] **[DEBT] 9 published `geometry` pointers in salt_lake_county CF are malformed and
  resolve off the page.** OBSERVED 2026-09-01 at the primary artifact (parsed every
  `pct:` box in `salt_lake_county/campaign_finance/{contributions,expenditures}.csv`;
  `screen_records.py` flags 6 of the 9 as warns, so the wave saw them and shipped anyway).
  The wrong values, verbatim: `Olson-Katie__BF2B7006` contributions L20
  `pct:3.12,59.57,86.76,-47.46@p5` — a NEGATIVE height, which is not a box at all;
  `Liewer-Ashley__7FF3AA93` L125–127 and `Liewer-Ashley__A20FF70B` L106–107 run past the
  bottom of the page (`y+h` up to 104.98); and 3 pre-existing clerk-legacy rows on
  `Winder_M12_June_Interim_Mayor_Redacted.pdf` do the same. **No money value is affected** —
  geometry is a provenance pointer (module CLAUDE.md: "a provenance pointer, never a value")
  — but a reader who renders these back gets nothing, and the repo publishes them as if they
  resolve. Terminating fix: re-measure the 9 boxes at the page (`make_snippet.py`), correct
  them in the owning wave records + re-materialize, or WITHDRAW them with the value intact
  under the W1 "frame corrected OR geometry withheld" rule; then add the box-validity check
  to `validate_finance.py` so a malformed pointer cannot ship again.

- [ ] **[DEBT] `make_snippet.py` mis-resolves `pct:` geometry on ROTATED pages — every
  geometry claim "proved" with it on a `/Rotate 90|270` page is UNPROVED.** OBSERVED
  2026-08-17 (weber wave; found INDEPENDENTLY by two chunk agents, then verified by me at
  the source): `scripts/campaign_finance/make_snippet.py` sizes its crop from the page size
  `pdfinfo` reports (line 68-75, `Page size: W x H pts` — the UNROTATED MediaBox) while
  `pdftoppm` renders with `/Rotate` APPLIED, so on a rotated page the axes are swapped and
  the crop lands off-target. Consequence: 4 weber records were withdrawn as "wrong
  geometry" on this tool's evidence and then REINSTATED when re-cropped against the
  rendered raster — all 8 sampled boxes reproduced exactly. The tool was NOT patched
  (frozen during the wave). Terminating fix: honour `/Rotate` when sizing the crop, then
  RE-CHECK any stored geometry previously validated with it on a rotated page (weber's
  rotated scans; the SLCo B2 and summit corpora used the same utility). Second, separate
  defect observed in the same pass: blank crops at high dpi on oversized-mediabox pages.
  **PARTIALLY CLOSED — the TOOL half is FIXED (verified at the source 2026-08-20):**
  `page_size_pts()` now returns the page **as poppler renders it**, with `/Rotate` applied,
  and documents why (`pdftotext -bbox` emits WORD coordinates in the same rotated frame while
  only its `<page>` header keeps the unrotated MediaBox). **The RESIDUAL is the corpus
  re-check** — stored geometry validated with the pre-fix tool on rotated pages in the SLCo B2
  and summit corpora — plus the separate high-dpi blank-crop defect. Weber's own 18
  withdrawals were re-measured and resolved in its 2026-08-18 close-out, and the utah wave
  (2026-08-20) measured 6,513 rows at 100% geometry against the FIXED tool, so neither of
  those corpora is implicated.
- [ ] **[DEBT] `index.csv` mislabels 7 salt_lake_county filings as County Council when the
  documents say SCHOOL BOARD — plus three smaller catalog defects in the same file.**
  OBSERVED 2026-08-20 (surfaced independently by TWO agents, then verified by the coordinator at
  the page): `salt_lake_county/campaign_finance/index.csv` carries 8 `FIFE-JEPPERSON, CHARLOTTE`
  rows, all labelled `office=County Council, seat=District 2`. The cover of
  `raw/easyvote/FIFE-JEPPERSON-CHARLOTTE__F2EC7ADF.pdf` (rendered and read) states **`Office
  Sought: Salt Lake School Board  District Number: 2`**. Her 2026 filing is genuinely County
  Council (she is a sitting school-board member who ran for the county seat), so the label is
  right for 2026 and WRONG for the 2024-cycle filings. **Reach is limited to the catalog**:
  `filing_totals.csv` holds only her legitimate 2026 row, so `cf_filing` in gov.db is clean, and
  the office gate correctly excluded her school-board itemized rows (73 C + 40 E) from
  `contributions.csv`/`expenditures.csv`. Three further defects in the same file, all flagged by
  the gate agent and none fixed (outside its write set): `snelgrove_R_Mayor_2031_YearEnd.pdf`
  carries `election_year=2030` from a filename-token mis-parse (adjudicated at the page in wave
  B2 as a Jan-2014 year-end for the **2012** county-mayor cycle); one filing carries
  `election_year=2000` / `date=2001-01-01` from an EasyVote `datesubmitted` placeholder of
  `01/01/01`; and 4 filings have a blank `seat` though the district is legible on the cover and
  already sits in the `vision/` cache. **GREW 2026-08-23 (wave W1) — a FOURTH class, in the
  newly-indexed `globalassets` channel: `seat` is WRONG, not merely blank.**
  `2018_disclosures__october__robert-cundick-10-30_redacted.pdf` carries `seat=At-Large A` while
  the form states **District 4** in BOTH office boxes; the consequence is not cosmetic — it puts
  Cundick in the wrong race and hides that he and Ann Granato were 2018 general-election
  opponents in District 4. `2018_disclosures__september__guyman-adam-council-at-large-c1.pdf`
  carries `seat=At-Large C` where the form reads "COUNCIL AT-LARGE" with **no letter at all**
  (the `c1` is the clerk's filename). Both found AT THE FORM by chunk agents not looking for
  them. Root cause identified: `characterisation.csv` records an `office_basis` per row proving
  the office came from the document, but has **NO equivalent basis column for `seat`** — which is
  how both slipped through. Terminating fix: correct the 7 office labels, the two mis-parsed
  years, the 4 blank seats AND these 2 wrong seats against each document's own cover, add a
  `seat_basis` column, **sweep all 130 globalassets seats** (two wrong found by chance in two
  small chunks is not a rate to extrapolate, but it is decisive evidence the column was never
  document-verified for this channel), then re-derive and re-federate.
  ⚠ The old line "natural home is the 2015–2021 harvest wave, which rewrites index.csv anyway"
  is retired: W1 phase 2 did NOT rewrite `index.csv` (phase 1 had already generated its 130 rows
  via `build_index.py`), so this remains open and unhomed.

Prior state: EMPTY as of 2026-08-01 — the st_george Larkin item filed earlier that day was
closed the same session (record: TODO_ARCHIVE anchor 2026-08-01-COUNTY-ACQUISITION).

New entries require a primary-source citation (see the rules above). The last three closures:

- [x] **Recommendation-oracle adjudication — ✅ DONE 2026-08-01.** 56 contradictions → **1
  documented source ambiguity** (the slc 2025-05-28 dual-direction motion, now
  caveat-carried as `dual-direction-recommendation`). Four regression-tested classifier
  iterations in db_build_lib + the 5 forks (denial-phrasing coverage incl. the MSD trailing
  "for denial" form; result-label vs motion-text precedence; dual-direction guard;
  weak-negation demoted below the result label; "(Final Action)" res now stages
  pc_final_action) + 6 evidence-cited disposition overrides for the item-text class
  (lehi 1, provo 3, white_city 1, magna 1). All 31 cities rebuilt; unit suite 14/14.
- [x] **bluffdale motion-text window — ✅ DONE 2026-08-01 (wave agent).** The defect was 4×
  the filing: 376 of 971 council motions had NO mover anchor (roster-gated window rewrite;
  9 genuine OCR-garble residuals remain, honest). Motion text rewritten on 948 council +
  292 PC motions with the vote layer PROVEN untouched (key-set identity, 0 value changes);
  person 56→29 (verb-contaminated surname movers healed); referral layer re-derived
  **269→38 links at census-adjudicated 100% precision** (every link individually verified;
  ledger 365→2 evidence-cited rows; Jordan Crossing links naturally; a second genuine
  Council↔RDA co-action surfaced).
- [x] **murray PC disposition audit — ✅ DONE 2026-08-01 (wave agent).** The ~300 post-audit
  PC motions ground-truthed; 7 wrong dispositions corrected via evidence-cited
  disposition_overrides.csv (vote layer proven untouched; 26 PASS / 0 FAIL); report:
  `murray_city_council/_audits/2026-08-01-pc-disposition-groundtruth/`. Extractor-class
  observations (footer-RE, tail-drop, the 'failed for a second' vocabulary nuance) filed
  in LEADS.md.

## [GATED] — owner decisions (do not start unprompted)

- [ ] **TRANCHE 3 PHASE B — remaining county itemization waves (per-wave approval).**
  SLCo legacy is DONE (2026-08-03); **juab 27, wasatch 111 and summit 116 all CLOSED &
  VERIFIED in the 2026-08-14..17 wave** (summit's queue closed 116/116 on 2026-08-17 and
  the owner ratified the reconciliation-basis rule that same day — LEADS.md 2026-08-17).
  **weber CLOSED & VERIFIED 2026-08-18** (98/98 filings itemized, 2,616 rows, 100%
  geometry, ZERO withheld). **utah CLOSED & VERIFIED 2026-08-20 — the largest Phase B corpus**
  (245/245 scanned filings over 247 reports, **6,513 rows**, 100% geometry, **ZERO withheld**;
  342 of 389 transcribed sides exact; $2.31M contributed / $2.23M spent).
  **WASHINGTON'S PARSER TRANCHE CLOSED & VERIFIED 2026-08-23** — its machine-readable era
  (106 of 206 filings) is done: all 102 born-digital Summary+ledger sets parsed, **3,256 rows**
  (1,518C + 1,738E) over 101 filings, 100% geometry, 1 side withheld, no page image read, and
  **0 of 206 `stated_*` values moved**. Its `election_year` question is CLOSED too — the column
  is document-stated by design (LEADS.md 2026-08-23), not a gap.
  **CACHE AND WASHINGTON BOTH CLOSED & VERIFIED 2026-08-24 — the Phase-B final wave.**
  washington **100/100** handwritten cover forms (530C + 778E, 100% `pct:` geometry, **ZERO
  withheld**, 173 of 200 sides exact) — the first Phase-B county with BOTH eras closed; cache
  **176/176** remaining distinct documents (556C + 1,119E transcribed → 756/1,466 published after
  the byte-duplicate fan-out, 100% geometry, **ZERO withheld**, 282 of 352 sides exact), which
  also closed the born-digital `cache_cfd` gaps. Both queues were **re-derived from the primary
  files** rather than inherited (washington's 100 reproduced independently of `index.csv.format`;
  cache's derived at the DOCUMENT grain — 239 index rows are 197 distinct sha256). Calibration
  pre-flight **21/21 per county**. Both rebuild byte-identical, `validate_finance` PASSes on
  both, **no `stated_*` moved**, and **no published `cf_cycle_county` total moved**.
  **SALT LAKE'S W2 CLOSED & VERIFIED 2026-09-01 — THE COUNTY ITEMIZATION PROGRAMME IS
  COMPLETE for every document the repo holds.** The EasyVote row-less residue was transcribed
  2026-08-24 by an EXTERNAL agent (Kimi K3) under `W2_HANDOFF.md` and verified + federated
  2026-09-01 by a Claude session: derived queue **240 = 238 transcribed + 2 school-board out of
  scope**, **18,240 rows** (11,852C + 6,388E), **100% `pct:` geometry**, **ZERO withheld**, and
  **141 previously-missing covers** (`cf_filing` 971 → 1,112). Per side: 359 exact · 33
  delta-with-cause · 82 `none` · 2 unknown · 4 out-of-scope. Independent verification before
  federation: all module gates re-run, **byte-identical rebuild**, pre-wave frozen blocks proved
  field-for-field unchanged (**0 `stated_*` moved**; the only movement inside rows 1–971 of
  `filing_totals` is 97 rows of the 2022 cohort gaining an itemized half), and **4 filings
  re-read at the page** — all reproduced exactly. Record:
  `salt_lake_county/campaign_finance/AVAILABILITY.md` § "The EasyVote residue" +
  `_backups/2026-09-01-w2-closeout/CLOSEOUT.md`.
  **THE ONLY COUNTY CF WORK LEFT IS ACQUISITION, NOT TRANSCRIPTION** — SLCo's 251 GRAMA-only
  online-filed 2015–2021 reports (W3), which require a records request, not a wave.
  Each wave runs the B2 production contract (calibration pre-flight incl.
  the corrected Rhodes specimen; arithmetic-first; pct: geometry; checkpoint discipline)
  and closes with a federation. Owner picks order + timing; specs live in each county's
  AVAILABILITY.md + the LEADS tranche-3 block.

- [ ] **RETRO-ANCHOR + BLIND-REVERIFY the scanned-source CF transcriptions (owner-amended
  2026-08-02: "eventually want to run it — snippet coordinates are essential; all the
  better if done independently so it verifies the data").** One program, two corpora,
  run under the calibration suite + the B2 production contract (tight-crop escalation,
  pct: geometry, crop-verify, page-subtotal gates, zero-glyph ruling):
  (a) **the scanned-city CF layer** — measured 2026-08-02: 13,358 vision-read contribution
  rows + 9,907 expenditure rows across the vision-cache cities (~68% of the city itemized
  layer; the 5,865+5,103 text-parsed rows get anchors ~FREE via deterministic re-parse
  with the geometry-emitting engine — do that tier first, no gate needed; the 558+771 API
  rows have no page origin, honest n/a);
  (b) **the tranche 1–2 county cover transcriptions** (~2,600 covers) — the original
  calibration-rerun question.
  DESIGN REQUIREMENT (owner): the re-read is **BLIND** — the transcriber never sees the
  existing values; anchors + values are produced independently, then DIFFED against the
  live layer. Agreement = the strongest independent verification these rows can get
  (correlated-error caveat noted — the calibration suite's Rhodes/field-shift specimens
  are the guard); every disagreement is adjudicated AT THE PAGE (make_snippet.py) before
  any value changes, through each module's documented correction path. Scale honestly:
  roughly 10× the county pilot; cost-decision remains the owner's per corpus/tranche.
- [ ] **Calibration-sample stage for any transcription-pipeline RERUN (owner note
  2026-08-02).** If the CF vision pipeline is ever rerun, build in a "select sample pages"
  calibration step (the Green Book enriched-pipeline pattern): a curated set of known
  difficult edge-case pages that every model/resolution/prompt configuration must pass
  BEFORE bulk transcription. Seed specimen #1 — the correlated-error case that
  agreement-gating cannot catch: **Shannon Rhodes's December-2018 Cache County fax, whose
  bistable open-top glyph reads differently at 150–200 dpi and whose two same-resolution
  passes would have "confirmed" each other.** ⚠ **This bullet's original ending — that a
  ≥600 dpi render of the cleaner October sibling copy settled it — was REVERSED on 2026-08-02
  and the sentence is corrected here (2026-08-23) to stop teaching the falsified lesson.** The
  sibling "settlement" endorsed the WRONG digit; the filing's own **arithmetic** decided it
  (Form A's 7 rows sum to exactly 1,694.09 and the cover closes only under a leading 1), and the
  published totals were corrected 4,799.09 → 1,799.09. The rule the specimen now carries is
  **ARITHMETIC CLOSURE OUTRANKS GLYPH READING AT ANY RESOLUTION** (GOTCHAS.md; documented at
  `cache_county/campaign_finance/CLAUDE.md` §"Render resolution matters"). Re-verified at the
  page on 2026-08-23 by both counties' pre-flights, one of which found a second bistable cell in
  the same filing that **stayed bistable at 900 dpi** and was likewise fixed by a printed sum. **The suite now EXISTS** (built 2026-08-02,
  tranche 3 Phase A): `_audits/cf-calibration-suite/` — 13 specimens (Rhodes fax +
  column-transposition, zero-vs-blank, currency-convention, page-decoy and
  completeness-gate classes, incl. negative controls whose correct answer is BLANK) +
  the pass protocol; grow it from each county's documented traps. This [GATED] item is
  therefore now only the RETROACTIVE question. ⚠ CAVEAT: adopting this
  properly may mean RERUNNING much of the completed OCR/vision transcription work
  (tranches 1–2, ~2,600 covers) under the calibrated configuration — a cost decision,
  not a defect; the existing layers remain valid as-audited until then.

- [ ] **CF adjudication hand-check** (2026-07-18: 11 corrected figures) + 2 open CF questions:
  bluffdale Hall Dec-04-final fold-in; holladay Tracy index date/label swap (rows 16-17 still
  carry the wrong dates).
- [ ] **GRAMA outreach** — ~110 genuinely-unpublished minutes across 13 cities, drafts ready;
  the only remaining channel (every public channel exhausted + documented). **SLC campaign
  finance now has its own send-ready package** (2026-08-14):
  `slc_city_council/campaign_finance/GRAMA_PREP_2026-08-14.md` — contacts, cost, statutory
  hooks, 2 paste-ready requests. **Owner decision: send or not.**
- [ ] **Whisper/audio transcription program** — scope decision (leads inventoried in LEADS.md).
- [ ] **Wayback archiving pass** — submit every sources.csv URL (~46.5k distinct) to
  web.archive.org; also the 26 cache_county Wayback rows with no snapshot URL.
- [ ] **STATE TIER reintegration** (owner ruling 2026-07-29): ut_state's 264 bills sit in
  `application` with zero purpose-built tables; ships v1 as-is with a README note (verified
  non-silent: gov_level + self-describing app_keys + 3 caveat rows). Design task, own terms.
- [ ] **Scope decisions:** orem RDA/MBA/BoA promotion (22 recovered docs, no repo layer);
  lehi advisory-committee bodies; SSL work-meeting "published vs unposted" ledger distinction;
  copperton 2025 seat-lettering question.

## Changelog

| date | what | record |
|---|---|---|
| 2026-09-01 | **SLCo WAVE W2 CLOSED — THE COUNTY ITEMIZATION PROGRAMME IS COMPLETE, and the repo's FIRST EXTERNAL-AGENT TRANSCRIPTION is federated.** The EasyVote row-less residue was transcribed 2026-08-24 by Kimi K3 under `W2_HANDOFF.md`; this session verified, federated and documented it. Queue **DERIVED** (every EasyVote filing with no advanced-search API rows): **240 = 238 transcribed + 2 school-board out of scope**, remaining **0**. Published **18,240 rows** (11,852C + 6,388E), **100% `pct:` geometry**, **ZERO withheld**, plus **141 previously-missing covers** — `cf_filing` for the county 971 → **1,112**, `cf_contribution` 24,352 → **36,204**, `cf_expenditure` 14,488 → **20,876**. Per side (480): 359 exact · 33 delta-with-cause · 82 `none` · 2 unknown · 4 out-of-scope. **Verified before federation, not after**: all module gates re-run independently, **byte-identical rebuild**, frozen pre-wave blocks proved FIELD-FOR-FIELD (contributions 1–24,352 and expenditures 1–14,488 identical; in `filing_totals` 1–971 exactly 97 rows changed, all the 2022 cohort gaining an itemized half, **0 `stated_*` moved**), and **4 filings re-read at the page** across the ledger tiers (exact, cover-only, the Wilson redaction, a delta) — all reproduced exactly, including the out-of-scope ruling re-proved at the cover. Reducer regenerated: **37 SLCo candidate-cycles moved GAP → PUBLISH** on the new covers, **0 moved back, 0 published figure changed value**, other 7 counties **0 rows changed**; `cf_cycle_county` 1,009 → **1,008** (the school-board row removed). Federation 44/44, integrity ok, FK 0, caveat 108; `check_doc_numbers` all PASS after 6 headline numbers updated. Two module-wide reading rules corrected in the same session: `donor_occupation` is **no longer paper-slice-only** (12,517 rows repo-wide, W2 10,225), and some expenditure amounts are **negative as printed** — take `abs()` before summing | `salt_lake_county/campaign_finance/AVAILABILITY.md` § "The EasyVote residue"; `_backups/2026-09-01-w2-closeout/CLOSEOUT.md` |
| 2026-08-23 | **COUNTY CYCLE REDUCER SHIPPED** — the 2026-08-02 "cf_cycle stays city-only" deferral is EXECUTED, not carried. New `cf_cycle_county` (**968** candidate-cycles across all 8 counties: **618** publish a figure, **350** honest GAP rows) + `v_cf_cycle_all` + `scripts/campaign_finance/cycle_totals_county.py` + a 31-case regression suite. Method: stated totals primary, a **balance-chain closure proof** as the resolver (it settles SLCo's markerless April-5 amendment trio to 142,340.79 with no heuristic), per-candidate regime detection where the county form prior can only confirm and never decide, **carryover separated and never subtracted** (159 cycles open with ~$1.70M carried in), **200 rows flagged `is_floor`** as lower bounds. The §0 landmine disarmed structurally: `cycle_totals.py` is now city-only by guard and the loader is `e.level`-gated, so a county file cannot reach `cf_cycle`. `cf_cycle`/`cf_filing`/`cf_contribution`/`cf_expenditure` proven BYTE-IDENTICAL; caveat 105→107; check_doc_numbers 13→19 checks, all PASS | `_backups/2026-08-23-cycle-reducer-impl/CLOSEOUT.md`; `scripts/campaign_finance/COUNTY_CYCLE_REDUCER_SPEC.md` |
| 2026-08-23 | **SLCo 2015–2021 PAPER SLICE CLOSED (wave W1 phase 2)** — 130/130 filings, 717 pages, **6,028 rows** (3,422C + 2,606E), 244 sides transcribed / 16 `none` / **0 withheld** / **0 amounts blank for illegibility**; 226 sides exact, 13 deltas each traced to a named page. Calibration pre-flight **21/21** (first run of the full suite). **Schema change shipped**: `donor_occupation` (owner decision 2026-08-20) — trailing-optional, 2,292 rows, SLCo-only; all 37 other CF modules byte-identical, 0 field diffs in the frozen pre-wave block. Build gained the **reconciliation-basis rule** after 4 revisions (prevented >$180k of fabricated deltas across 6 filings); 284 unverifiable geometry pointers WITHDRAWN with values intact. ⚠ 1 owner decision filed (a county PDF's redaction is cosmetic); the index.csv [DEBT] GREW (2 wrong seats + no `seat_basis` column) | `_backups/2026-08-23-slco-w1p2/CLOSEOUT.md`; AVAILABILITY §'The 2015–2021 PAPER slice' |
| 2026-07-31 | Restructure: TODO 3,786→this file; options/watches/tails → LEADS.md; gotchas → GOTCHAS.md; HANDOFF → single banner; NEXT_SESSION_PLAN retired; 62 stale-already-done items closed + 25 non-items dropped per verified triage | `TODO_ARCHIVE.md` anchor 2026-07-31; `_audits/2026-07-31-publication-review/` |
| 2026-08-01 | DEBT queue EMPTIED: recommendation-oracle 56→1-documented (classifier v2.3.1 + 6 overrides + slc caveat); bluffdale window rewrite (376-motion anchor defect, referrals 269→38 @ 100% census precision, ledger 365→2); murray PC audited (7 overrides) | `TODO_ARCHIVE.md` anchor 2026-08-01-FINALE |
| 2026-08-01 | DEBT-clearance wave: 12 of 14 items closed (10 Opus agents + solo; 5 premise-failures, 2 collateral recoveries, bluffdale referrals 269→62); 2 NEW evidence-cited items filed (2021 RCV mislabel class; bluffdale motion-window) | `TODO_ARCHIVE.md` anchor 2026-08-01 |
| 2026-07-31 | holladay Layton [DEBT] closed — the requested `person-ambiguity` caveat row shipped with the G2 back-fill (verified live in gov.db) | caveat: holladay/planning_commission/person-ambiguity |
| 2026-08-01 | COUNTY DATA ACQUISITION package DONE (9-agent wave + solo): SLCo even-year elections 2002–2026 (election_race 810 / election_result 5,820) + 8 county CF datasets (~2,270 filings); st_george Larkin [DEBT] found+fixed+closed same session; federation gates 44/44, doc checks 13/13, marquee 5/5 | `TODO_ARCHIVE.md` anchor 2026-08-01-COUNTY-ACQUISITION; per-county RECON/AVAILABILITY files |
| 2026-08-03 | WAVE B2 QUEUE CLOSED + CONSOLIDATED FEDERATION: 496/496 clerk-legacy filings itemized (22,871 rows; 855 sides exact / 80 filer-arithmetic deltas verbatim / 8 documented no-schedule gaps ~$121k+$120k; survived 2 session-limit + 3 network kills on checkpoint discipline; the closer overturned an inherited 'no gate available' claim and closed both withheld sides EXACT on the attachments' own last-page totals). Federated with the Rhodes correction + SLC city's first 8 filings: cf_contribution 40,115 / cf_expenditure 28,274 / cf_filing 3,810 — 44/44, integrity ok, doc checks PASS, marquee 5/5 | closer report; salt_lake AVAILABILITY.md final state |
| 2026-08-02 | WAVE B2 (SLCo legacy itemization) CHECKPOINT-CLOSED: 238/496 filings → 10,561 donor/vendor rows (208+204 sides exact, 35 deltas all filer-traced, 0 withheld, 3 illegible cells), pilot's 24 promoted, EasyVote block byte-unchanged, validator PASS; 258-filing residue enumerated + resumable; county redaction imperfections documented in PRIVACY.md; 2 Romero filings missing schedule pages at the SOURCE (~$119k floor, GRAMA lead) | `_backups/2026-08-02-tranche3/slco-b2/`; docs synced |
| 2026-08-02 | RHODES GLYPH REVERSED (found by B2's pre-flight arithmetic gate; coordinator-adjudicated with 3 independent proofs incl. Form A's own sum 1,694.09): the 600dpi sibling "settlement" on '4' was the eagerness failure INSIDE the escalation path — published cache totals corrected 4,799.09→1,799.09 (both Rhodes rows), calibration specimen + README + GOTCHAS + cache CLAUDE all rewritten to the sharpened rule: ARITHMETIC CLOSURE OUTRANKS GLYPH READING AT ANY RESOLUTION | cache vision caches 00b019d3/bc7ce2f3 (adjudication notes); corrected values federate with the B2-residue close-out |
| 2026-08-02 | SLC CITY CF FALSIFIED-NEGATIVE + FIRST ROWS (owner-directed hunt): the "no PDFs exist / portal is sole source" determination overturned — 8 born-digital 2003 Recorder filings recovered via Wayback (Anderson mayoral $127k incl. itemized donors) + STRUCTURED same-day (222 contributions + 162 expenditures, 8/8 + 6/8-with-2-honest-unknowns reconciled, geometry-anchored, validate PASS 0/0); state-tree/county/PMN negatives now EARNED (667 files classified); portal DB proven ALIVE behind an app-level 503 → 2005–2025 = GRAMA-shaped + twice-daily API watcher armed; cf-honest-zero caveat rewritten (federates with the B2 close-out build) | `slc_city_council/campaign_finance/RECON_2026-08-02.md`; rows enter gov.db at next federation |
| 2026-08-02 | TRANCHE 3 PHASE A DONE (owner-approved): calibration suite built (`_audits/cf-calibration-suite/`, 14 specimens incl. negative controls + the field-shift lesson); 6 shared county form families + 2 driver capabilities (48/48 tests; 90/90 city CSVs byte-identical, manifest digest proven); born-digital itemization sweep — 1,311 reconciliation-gated geometry-anchored rows over 82 filings in 6 counties (cf_contribution 25,147 / cf_expenditure 19,987), 3 family bugs documented+gated for Phase B; caveats + docs synced; federation 44/44, doc checks PASS | family tests `scripts/campaign_finance/tests/`; per-county module docs; LEADS Phase-B residuals |
| 2026-08-02 | VISION-TOTALS TRANCHE DONE (owner-approved 7-agent wave, survived a session-limit kill + a network outage on checkpoint discipline): every county CF cover read — cf_filing now carries 1,911 county stated-totals rows (slco 834 · utah 265 · cache 239 · washington 206 · summit 131 · wasatch 111 · weber 98 · juab 27); offices resolved (cache 128→0, washington 48→7-county, utah 19→8+4+7); juab conformance 37-fails→PASS; wasatch form_family reclassified at builder (6 misfiles); summit anti-transposition audit 17/17 exact + crop-defect date recovery (+45); cf_cycle kept CITY-ONLY by design; caveats rewritten (104 rows); federation 44/44, doc checks 13/13, marquee 5/5, city cf rows byte-identical | per-county AVAILABILITY.md verification sections; LEADS.md wave-leads block |
| 2026-08-24 | **PHASE B COUNTY ITEMIZATION COMPLETE — cache + washington CLOSED** (owner-approved final wave). Queues **re-derived from primary files, not inherited**: washington **100 documents / 401 pages** (reproducing the 95-scanned + 5-mislabelled-`text` split WITHOUT using `index.csv.format`), cache **176 distinct documents / 647 pages** at the DOCUMENT grain (239 index rows = 197 distinct sha256), which included **16 born-digital filings the `cache_cfd` parser had left row-less**. Calibration pre-flight **21/21 per county** (2 fresh runs; cache's settled the Rhodes specimen with the sibling copy NEVER OPENED, and found a second bistable cell in the same filing that only a simultaneous two-cell closure resolves). Published: washington **530C + 778E**, cache **556C + 1,119E** transcribed (756/1,466 after the byte-duplicate fan-out) — **100% `pct:` geometry, ZERO sides withheld, 0 amounts blank for illegibility, 455 of 552 sides exact, 38 filer-arithmetic deltas verbatim, 59 `unknown` where the page prints no anchor of any scope**. Two 100x fabrication hazards found and closed IN THE BUILD before any row shipped: handwritten **space-separated cents** (`63 75` → 6375 under every module's space-stripping `dec()`) and **decimal commas** (`300,00` → 30000), now read by the new shared `common.parse_vision_amount`, which still refuses the malformed decimals the `utah-malformed-decimal` specimen requires to stay blank. Also corrected in the layer that owns it: **36 washington `index.csv` candidate names that were tesseract noise**, via a new `candidate_determinations.csv` on the `office_determinations.csv` contract (bounded by column-diff: 36 rows x 3 derived columns, 0 other values moved). Verification: both modules **rebuild byte-identical**; `prove_additive` **0 moved values, no `stated_*` or `amount` touched**; an independent cross-check of the build's own sums against each transcriber's recorded sum agrees on **468 of 469 comparable sides** (the one divergence is a filer who excluded a loan from his printed total, and it publishes correctly as a delta); `validate_finance` **PASS** on both (38 PASS + 1 known non-regression repo-wide); 93 family tests; federation **44/44**, integrity ok, FK 0, caveat **108**; `check_doc_numbers` **all PASS** after correcting a `cf_cycle_county` drift (968→1,009) the earlier SLCo W1 wave had left behind. **`cf_cycle_county` published totals UNCHANGED in both counties**; only the itemized cross-check improved (washington 0→15 cycles, cache 5→50). | `washington_county/campaign_finance/AVAILABILITY.md` §10; `cache_county/campaign_finance/AVAILABILITY.md` "QUEUE CLOSED"; `_backups/2026-08-23-cache-washington-cf/CLOSEOUT.md` |
| 2026-08-23 | **WASHINGTON PARSER TRANCHE CLOSED** (owner-approved): its machine-readable era itemized and closed — queue DERIVED from `index.csv` (106 machine-readable filings of 206, **not** the 314-file sizing; the vision residue is **100** filings, because 5 the index calls `text` are image-faced), all 102 born-digital sets parsed → **1,518 contribution + 1,738 expenditure rows** over 101 filings, **100% geometry** (2,659 `.xls` cell refs + 597 `pct:` boxes from `pdftotext -bbox-layout`), 57 sides stated-exact / 63 cumulative-exact (`reconciles_*` honestly BLANK) / 42 filer-arithmetic deltas verbatim / 41 empty schedules / **1 withheld** (`$5,00.00` export typo). Four reading-path defects fixed AT EMISSION — multi-page `-layout` column drift (cost 54 of 77 rows on one filing), dropped in-kind/loan columns, a second stacking layout that would have shipped STREET ADDRESSES as `donor_raw`, and the SCHEMA.md §2a caveat-1 multi-file `source_filing` bug. Every previously-published row preserved at an identical amount; **0 of 206 `stated_*` moved**; rebuild byte-identical; 7 new family tests (62 pass); federation 44/44, FK 0, doc checks PASS | `washington_county/campaign_finance/AVAILABILITY.md` §8–§9; `_backups/2026-08-23-washington-cf/CLOSEOUT.md` |
| 2026-08-20 | **UTAH WAVE B2 QUEUE CLOSED — the largest Phase B corpus**: 245/245 scanned filings itemized over 247 reports (2,884 contribution + 3,629 expenditure rows, **100% pct:-geometry-anchored, ZERO sides withheld**; 342 of 389 transcribed sides EXACT, 34 filer-arithmetic deltas each traced, 11 cumulative-exact left honestly BLANK not True; $2.31M contributed / $2.23M spent). Prereqs first: 6 rowbands/fitgrid defects fixed + promoted to `scripts/campaign_finance/`, 13/13 calibration pre-flight (suite 13→21 specimens), and the claimed bound-in 2018 Schedule B **verified FALSE** at the source. Wave found 7 invisible row-index traps, 10 causes of a blank donor city/state, and a ghost-page screen that prevented 14 fabricated rows; a `recon_delta_*` derivation the coordinator introduced was caught as a scope error and REVERTED. Federation 44/44, validate_finance PASS, validate_entity 13/1/0, rebuild byte-identical, cover tranche provably unmoved | `utah_county/campaign_finance/AVAILABILITY.md` "QUEUE CLOSED 2026-08-20"; `_backups/2026-08-18-utah-cf/workdir/` |
| 2026-08-20 | utah_county Smith 2014 `stated_beginning_balance` [DEBT] filed AND closed same session: page prints `$3446` with no decimal point (transcript was faithful — the FILER omitted it), value proved **34.46** three ways (line 5 subtotal 1,500.00 − line 4 1,465.54; line 7 closes at 0; the prior report's line 7 = 34.46, which the form's own arrow points at). Fixed via `vision/a0202d15.json` + rebuild; verbatim `3446` retained in totals_verbatim; balance chain now continuous | `TODO_ARCHIVE.md` anchor 2026-08-20-UTAH-B2-CLOSE |
| 2026-08-20 | **salt_lake_county EasyVote office-gate [DEBT] filed AND closed same session** — the gate resolved offices only through a snapshot of currently-ACTIVE offices, so 12 historical `OfficeGuid`s fell through and their rows were dropped silently. Fixed GUID-first (metadata fallback); **contributions 19,702→20,930, expenditures 11,403→11,882** (+$270,619 / +$375,419), 0 rows lost, cover tranche provably unmoved, zero school-board rows admitted. The 26 filings that gained an itemized half **reconcile EXACTLY on all 52 sides** — vision cover reads matching born-digital API rows to the cent. Docs reconciled; 1 new [DEBT] filed (index.csv school-board mislabel) | `TODO_ARCHIVE.md` anchor 2026-08-20-SLCO-EASYVOTE-GATE |
| 2026-08-20 | **salt_lake_county is NOT finished — sized, not guessed.** Portal probe: channel (b) is a DEAD APPLICATION, not a WAF block (path-selective RSTs; real Chrome resets; Wayback 200s end 2026-01-15) — no browser route exists, **GRAMA only** for its 251 online-filed reports, draft written. But **130 unacquired 2015–2021 county-office PDFs are freely downloadable today** from the county CMS `globalassets` path (zero overlap with the 547 held; AVAILABILITY.md knew the host only from the metro-township page and filed it as an out-of-scope BONUS). Residue audit: of 240 row-less EasyVote filings, **197 carry real detail (~18,433 rows over 980 pages)** — a GAP, not an honest zero — and 143 have no `filing_totals` row at all | `_recon/2026-08-20-portal-probe/`; `_audits/2026-08-20-easyvote-residue/` |
| 2026-08-20 | **`rowbands.py` DEFECT 7 [DEBT] CLOSED** — reproducer now returns 16 rules (top at 16.25 pct vs the wave's crop-proved 16.30) + 5 verticals; `--no-normalize` reproduces the old answer, isolating the cause. **The filed CAUSE was wrong in 3 places** (a `fill>=0.80` gate from a prior fix splits the rule into 0.71+0.40 runs and discards both; the vertical failure is page SHEAR, not threshold; the false bands came from the footer box, not the subtotal underline) — the numbers were exact. Regression: 180 pages / 6 counties / 1,942 wave-proven boxes, containment 1,048→1,072, **no county lost containment**. Four honest geometry states added with nonzero exit | `TODO_ARCHIVE.md` anchor 2026-08-20-ROWBANDS-DEFECT7-CLOSED |
| 2026-08-20 | **W1 phase 1 done: 130 paper-filed 2015–2021 SLCo filings acquired** (0 failures, sha256-verified, 717 pages) and `index.csv` made REPRODUCIBLE — `build_index.py` knew only 2 of 3 channels, so the documented rebuild silently deleted all 130 rows. Fixed + proved byte-identical (1,119 rows, deterministic). **A second `has_itemized` defect was caught by the agent against the coordinator's wrong brief**: only 33 of 130 flips were the office-gate repair; the other 97 came from computing the flag off `filing_totals` membership (which includes 670 stated-totals-only vision rows) and would have asserted itemization on the audited row-less 2022 residue. Predicate fixed to `n_contrib_rows+n_expend_rows>0` → **197 yes / 245 no**, matching the documented split | `_audits/2026-08-20-globalassets-harvest/` |
