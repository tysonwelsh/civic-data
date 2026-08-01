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
- [ ] **G9. Declare against SHIP_GATE.md → publish provisionally** (public repo + gov.db.gz
  release + Zenodo DOI + municipalsky.com link). Then: [DEBT] → GitHub issues; leads stay in
  LEADS.md or become unmilestoned enhancement issues; honest ceilings NEVER become issues.

## [DEBT] — correctness queue (wrong or missing values; evidence-cited)

- [ ] **Legacy `recommendation` contradicts disposition∘outcome on 56 PC rows** (25 entities;
  was ~68 pre-G8b). Analysis 2026-08-01: `recommendation_of()` is an INDEPENDENT keyword
  derivation serving as a validation oracle vs `_compose_dir(disposition,outcome)` — the 56
  are the oracle firing. Visible classifier gap: negation phrasings ("recommend that X not
  be approved") fall through to the bare-"recommend" → Positive default (the
  herriman/murray/SJ deny-pattern cluster); the Positive+approve+Fail pattern (24 rows) is
  the matcher reading direction words on a motion that FAILED. Fix = refine
  `recommendation_of()` in db_build_lib (+ 6 fork ports) + per-row source adjudication of
  the remainder; touches ~20 entities + re-federation.
- [ ] **[NEW 2026-08-01] 2021 RCV mislabel class — 9 race rows in 3 entities** (found by the
  SSL wave agent cross-checking the county's official 2021 Ranked Choice Results report,
  `sandy_city_council/election_results/raw/2021-general-election-ranked-choice-summary-report.pdf`):
  cottonwood_heights Mayor + D3 + D4 labeled 'plurality' (the Mayor race went FOUR RCV
  rounds — Weichers 3,526 first-choice → 4,619 final vs Kraan 3,017 → 4,117, so stored
  first-choice margins are actively misleading; CH's election_results/CLAUDE.md ~131-132
  affirmatively asserts CH did not join the pilot, contradicted by the primary source);
  magna Metro Township D2 (p.21); slc D1/D2/D3/D5/D7 voting_method blank (pp.11-15).
  holladay/riverton/south_jordan/kearns/copperton/alta verified correctly excluded.
- [ ] **[NEW 2026-08-01] bluffdale motion-text window captures the agenda-notice preamble
  instead of the motion sentence on 94 motions** (52 council + 42 PC; motion_no=1 class) +
  ~43 in-session RDA/LBA motions windowed onto adjournment/roll-call blobs — the root cause
  of 313 of the 365 referral-override suppressions (bluffdale wave agent, 2026-08-01;
  flagged-not-fixed per the layer rule). Fixing the extractor window would let most of the
  override ledger be deleted; until then the ledger is LOAD-BEARING and re-extraction
  renumbering will fail its app_keys loudly (regenerate the ledger, protect the Jordan
  Crossing pair — see bluffdale db/CLAUDE.md). Bluffdale referral RECALL is unmeasured
  (the 2026-08-01 pass removed false links only).
- [ ] **~300 murray PC motions postdate the disposition ground-truth audit** — dispositions
  computed but unaudited; fold into the next /audit-city-data pass. (Triage L2153.)

## [GATED] — owner decisions (do not start unprompted)

- [ ] **CF adjudication hand-check** (2026-07-18: 11 corrected figures) + 2 open CF questions:
  bluffdale Hall Dec-04-final fold-in; holladay Tracy index date/label swap (rows 16-17 still
  carry the wrong dates).
- [ ] **GRAMA outreach** — ~110 genuinely-unpublished minutes across 13 cities, drafts ready;
  the only remaining channel (every public channel exhausted + documented).
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
| 2026-07-31 | Restructure: TODO 3,786→this file; options/watches/tails → LEADS.md; gotchas → GOTCHAS.md; HANDOFF → single banner; NEXT_SESSION_PLAN retired; 62 stale-already-done items closed + 25 non-items dropped per verified triage | `TODO_ARCHIVE.md` anchor 2026-07-31; `_audits/2026-07-31-publication-review/` |
| 2026-08-01 | DEBT-clearance wave: 12 of 14 items closed (10 Opus agents + solo; 5 premise-failures, 2 collateral recoveries, bluffdale referrals 269→62); 2 NEW evidence-cited items filed (2021 RCV mislabel class; bluffdale motion-window) | `TODO_ARCHIVE.md` anchor 2026-08-01 |
| 2026-07-31 | holladay Layton [DEBT] closed — the requested `person-ambiguity` caveat row shipped with the G2 back-fill (verified live in gov.db) | caveat: holladay/planning_commission/person-ambiguity |
