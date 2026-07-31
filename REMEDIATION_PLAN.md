# Remediation & Standardization Plan

Source: repo-wide audit `_audits/2026-07-02/report.md`. Phases run in order — repairs
before standardization (never standardize on top of broken data), standardization before
hardening. Originals of every modified file are copied to `_backups/2026-07-02/<relative
path>` before change. Principle throughout: **never overwrite a city-faithful value; add
normalized fields alongside. Honest gaps over invented data.**

## Phase 1 — Repair (fix confirmed defects)

- [x] **1.1 Sandy PUA recovery.** DONE 2026-07-02: 63/63 decoded (verified 1.000 vs raw
      PDFs); motions 655→833, vote rows 2,974→3,975, contested 79→131; 2022/2023
      voting-meeting counts back to normal (35/36). Bonus: roster was missing appointed
      member Scott Earl — 155 silently dropped rows restored (some in never-garbled
      files). The "16 page-break Aye drops" were actually narrative voice-vote tallies
      (names never printed in source) — honest gap, documented. db untouched by design
      (built from Legistar API, not minutes); weeks rebuilt. Decode the 63 U+F0xx-garbled minutes (subtract 0xF000),
      verify decoded text against retained raw PDFs, re-run vote extraction (recovers
      ~190 motions / 121 roll calls, 2021–2023), fix the 16 documented page-break
      Aye-list drops if tractable, rebuild sandy db + weeks, update docs/VERIFICATION.
- [x] **1.2 Ogden 2022 re-carve + re-OCR.** DONE 2026-07-02: all 296 pp re-rendered at 300 dpi
      + tesseract 5.5, re-carved on meeting-opening paragraphs (running-header cross-check:
      0 mismatches) → 42 → 73 files / 30 → 38 meeting dates (every missing date recovered,
      + bonus 2022-05-10); screener 2022 med_split 24.3 → 0.0; named roll calls 66 → 95 and
      ≤5-of-7 share 41% → 12% (remainder all match "Excused:" lines); ~33 motions mis-tagged
      RDA corrected to Council (2022 truly has 0 RDA/MBA — separate 2022 sets never acquired,
      now documented alongside 2023's); non-2022 vote rows byte-identical; db + referrals
      (id-pinned overrides re-bound) + weeks + speaker log (581→635) rebuilt; docs' wrong
      "2023 is OCR" and "coverage complete" claims corrected; 2 clerk-typo dates resolved by
      header+weekday and preserved verbatim. Details: ogden VERIFICATION.md "Remediation 2".
- [x] **1.3 Vineyard wrong/duplicate docs.** DONE 2026-07-02: all four documents recovered
      (no unrecovered entries needed) — real 2020-06-24 + PC 2023-06-21 fetched from PMN
      (CivicClerk's only Minutes attachments are city-side mis-uploads of Feb-26 / Jun-7),
      2020-09-23 stub recovered via OCR of fileId 905 (scanned copier PDF), 2023-08-30 stub
      via pdftotext of fileId 1345; 2024-04-10 deduped (kept `city-council-meeting.md` —
      body titles itself REGULAR MEETING and contains the work-session content). Council
      votes 5,126 → 5,240 rows (−71 dup/wrong, +185 recovered; unaffected rows
      byte-identical), PC 1,619 → 1,617 (−10 dup, +8 real); db (1,417 motions · 6,857
      votes · INTEGRITY OK) + weeks (150) rebuilt; the 173/165/138 meeting-count claims
      reconciled to 172 (163 council + 9 RDA). Screener: duplicate_bodies 0, stubs 0.
      Details: vineyard VERIFICATION.md 2026-07-02 addendum.
- [x] **1.4 St George 2025-10-09.** DONE 2026-07-02: real work-meeting minutes NOT
      recoverable — the published `2025.10.09 Work Meeting Minutes.pdf` is the same wrong
      file (md5-identical to 10-16's minutes) on BOTH Revize and PMN; wrong doc + index row
      removed, meeting logged in new `meeting_minutes/minutes_unrecovered.csv` (the meeting
      was real: agenda/packet/2 recordings exist). 110-vs-70 explained: 70 of the 110 rows
      dated 10-09 were misdated duplicates from the wrong file (removed); the other 40 are
      the genuine, separate 10-09 REGULAR meeting (verified 0.998-similar to PMN's copy;
      kept). Votes 8,382 → 8,312 (remaining rows identical); `db/referral_overrides.csv`
      remapped to post-repair application_ids so the referral layer reproduces its 117
      links exactly; db + weeks (248) rebuilt. Screener: duplicate_bodies 0, stubs 0.
      Details: st_george VERIFICATION.md 2026-07-02 addendum.
- [x] **1.5 Provo comment truncation.** DONE 2026-07-02: form-feed cut replaced with a
      page-walk classifier (STOP on new-document/email/eComment headers, JOIN on
      mid-sentence continuations, signature-aware ambiguity rule). 19/81 rows changed;
      old text a strict prefix of new in all 18 extensions; function-word endings 6→0;
      bleed check 0/81; every row verified a verbatim contiguous substring of raw packet
      text. 3 remaining unsigned endings are source-faithful (letters end in the writer's
      own attachments). weeks/ rebuilt (14 bundles changed); CLAUDE.md history corrected. Replace the first-form-feed-past-200-chars cut
      with a page-continuation join; re-extract from retained `raw/packet_txt/`; verify
      the known-truncated letters (McCoard, Steed, Bogdin) now complete; document the fix.
- [x] **1.6 Park City derived layers.** DONE 2026-07-02: db build now fail-loud (plain
      INSERT + db/vote_overrides.csv; 9 conflicts documented, 0 arbitrary); both mayoral
      tie-breaks in parkcity.db via new `vote.note` column; reconciliation printed every
      build (7,989 CSV = 7,980 db + 9 merged overrides). Extractor case-sensitivity fix
      removed the Orlando-URL motion **plus 9 more spurious motions of the same class**
      (incl. one fabricated Recuse row): motions 1,567→1,557. weeks/ rebuilt — 459
      comments now bundled (was 0). Docs reconciled. Make the db build stop silently dropping rows:
      both mayoral tie-breaks must exist in `parkcity.db`; the 9 contradictory Aye+Nay
      pairs get an explicit, documented resolution (overrides file — never arbitrary);
      remove/flag the spurious Orlando-URL motion; rerun `build_weeks.py` (fixes 0-vs-459
      comments staleness); fix doc-vs-data drift (tie-break count, motion count, referrals).
- [x] **1.7 Small fixes.** DONE 2026-07-02. Logan: RDA tail restored AND the 10 stranded
      lines removed from the council file (splitter bug documented; script not in repo).
      Nephi PC 2024-01-10: 167→0 U+FFFD (the font renders tofu visually too — recovery
      was deterministic contextual restoration, one flagged judgment call "se�ng"→
      "setting"; source typos preserved); 2022-01-19: 6→0 (Wingdings arrows → "→").
      Votes re-verified byte-identical. Known leftover: Nephi PC footer bleed in motion
      text (unrelated extractor issue, documented).
- [x] **1.8 Doc-drift sweep** DONE 2026-07-02 (SLC/WVC/WJ): every number re-measured,
      not copied. Notables: SLC README's PC recommendation/final-action split was
      materially off (now 252 recs = 211+41 / 290 final / 198 procedural); SLC comment
      counts refreshed (13,334); WVC raw-retention claim replaced with verified re-fetch
      path (3/3 sampled source_urls live); WJ "no OCR" corrected with file-level evidence;
      stale `extract_votes 2.py` + orphan .pyc removed (backed up). Leftover for later:
      `st_george_city_council/meeting_minutes/CLAUDE 2.md` stale duplicate (left for the
      St George agent's scope). (claims contradicting data): SLC README "scaffold only" +
      stale comment counts; West Valley "raw/ retained" claim; West Jordan "no OCR";
      Sandy PC phantom `minutes/` claim; Nephi format metadata; stale duplicate script
      `provo .../extract_votes 2.py`; orphan `.pyc`.
- [x] **1.9 Verify.** DONE 2026-07-02: independent screener sweep across all 26 minutes
      corpora post-repair — repaired cities clean (Sandy CLEAN, Ogden split-outliers
      44→2, duplicate_bodies 0 repo-wide outside verified-distinct pairs). Remaining
      known-benign flags: SLC 2020 OCR (27 files, documented grade B) and source-exhibit
      artifacts (park_city, logan PC).
      **Follow-up repair DONE 2026-07-02:** the repo-wide duplicate-body screen surfaced 12
      missed identical-body groups — lehi (8 Granicus double-event pairs; −265 council /
      −54 PC vote rows; referrals 474→459, all deltas IDF-traced), nephi (wrong-doc
      2021-02-23 → real minutes recovered from PMN; −5/+1 rows), orem (wrong-doc PC
      2025-10-15 → unrecoverable, removed+logged; 0 row delta, both parsed tally-only),
      west_jordan (2022-06-22 parsed twice; −78 rows). All verified md5-identical at source
      first; dbs/referrals/weeks rebuilt; screeners now duplicate_bodies=0 on all four
      corpora (lehi 2024-06-18 pair re-verified as two real meetings, kept). Addendum
      appended to `_audits/2026-07-02/report.md`; detail in each city's VERIFICATION.md.

## Phase 2 — Standardize (comparability without distortion)

- [x] **2.1 Repo root layer.** DONE 2026-07-02: root `README.md` (13-city map, standard
      layout, join keys, coverage caveats, expansion datasets) + `CLAUDE.md` (artifact
      selection, cardinal rules, cross-city comparison rules, per-city quirk one-liners)
      + `SCHEMA_SPEC.md` (layout, 13-col all_votes + minutes_index schemas, vote-value
      vocabulary with measured per-city ceilings, db schema incl. sandy fork / park_city
      vote.note, weeks conventions, provenance, and the 2.2–2.4 normalization contract
      verbatim) + `scripts/validate_city.py` (9 checks a–i, stdlib-only, never mutates;
      exit code = FAILs) + `scripts/build_coverage.py` → `coverage.json` (13 cities ×
      109 dataset entries, everything measured from files). Validator run on all 13:
      **0 FAIL everywhere** (4 clean; 9 with honest WARNs — documented extensions, the
      SLC PC legacy minutes_index schema, and 15 repo-wide duplicate (source,motion_no,
      date,member) CSV rows that exactly explain every db-vs-CSV delta: slc 6, ogden 3,
      st_george 3, nephi/provo/west_jordan 1 — left for a later fix pass, data not
      touched). Bonus corrections found by measuring: St George minutes actually span
      2020– (2020–21 are PMN backfill, not missing); west_jordan PC names only
      dissenters/absentees (zero named Ayes). motions_std.csv files (landed by the
      parallel 2.2/2.3 agent) validate against the contract in all 26 datasets; sandy
      PC's constant provenance string makes (source,motion_no) degenerate there —
      documented in SCHEMA_SPEC §2, validator joins on (source,motion_no,date).
- [x] **2.2 `result` normalization.** DONE 2026-07-02: `scripts/normalize_motions.py`
      (stdlib-only, deterministic, idempotent) parses all **378 distinct result strings**
      across the 26 all_votes.csv files into per-motion `motions_std.csv`
      (outcome/tally_aye/tally_nay/tally_other/vote_mode beside verbatim `result_raw`);
      one shared cascade + 6-entry exceptions table for true one-offs. Outcome coverage
      **99.4% repo-wide (22,980/23,110)**; 24/26 files at 100%; stragglers: ogden mm
      91.6% (126 `Recorded` = OCR-garbled narrative outcomes, honest unknowns) and sandy
      mm 99.5% (4 bare `Voice`). Tally cross-check vs counted member rows: 100% in 9
      cities; provo 90.4% / west_jordan 82.0% / sandy 98.5% are the documented
      dissent-only-naming source styles (every disagreement class inspected). Details:
      `crosswalks/README.md`.
      Original scope: Keep `result` verbatim; add parsed columns
      alongside: `outcome` (pass/fail/died/withdrawn), `tally_aye`, `tally_nay`,
      `tally_other`, `vote_mode` (roll-call/voice/unanimous-declared). One shared parser
      with per-city format profiles; unparseable strings flagged, never guessed.
- [x] **2.3 Vote-taxonomy standardization.** DONE 2026-07-02:
      `crosswalks/motion_type_crosswalk.csv` covers **all 197 observed (city, native
      motion_type) pairs** (SLC variants, the 5 PC bespoke taxonomies, the shared clone
      set; uninformative labels map to blank); `motions_std.csv` adds `motion_type_std`
      (13-value enum) + `land_use_type` (11-value sub-taxonomy) for all 23,110 motions
      via crosswalk + one uniform ~40-rule text classifier (every rule id recorded in
      `classify_method`; rules override the crosswalk top-level only on high-confidence
      patterns; no signal → Other/low, never guessed). `action_class`
      (recommendation/final-action/procedural) extended to all PC + council datasets;
      SLC PC's own audited column mapped through verbatim. **Hand-verified 390 motions
      over 3 iterate-fix rounds; final fresh 130-motion stratified sample: 128/130
      (98.5%)** — both residual errors documented in `crosswalks/README.md`. Ogden↔Lehi
      land-use skew partially closed (sandy PC `Planning Item` blob now fully typed;
      subject-bearing ogden motions reclassified); the honest residual: 428 ogden
      council adoption motions whose *entire* captured text is "ORDINANCE WAS PASSED
      AND ADOPTED AS ORDINANCE 20xx-N" — subject exists only in un-captured agenda
      headings (re-extraction job, noted for Phase 3). Distribution table + per-city
      explanations: `crosswalks/README.md`. Original scope:
      - Crosswalk table for label variants (SLC's 5 spelling variants; PC synonym
        clusters like `Conditional Use Permit`/`Conditional Use`, `Zoning Text Amendment`/
        `Zone Text Amendment`/`Ordinance Text Amendment`/`Code/Ordinance Amendment`).
      - **`motion_type_std`: re-derive one standardized category for all ~24k motions
        with a single classifier applied uniformly across all 13 cities** (from motion
        text/title), stored beside the city-native `motion_type`. This is the only honest
        fix for application skew (Ogden files rezones under `Ordinance`, Lehi under
        `Land-Use/Zoning`; Sandy PC is one `Planning Item` blob). Include a standard
        land-use sub-taxonomy: Rezone / Code-Text Amendment / General Plan Amendment /
        Subdivision-Plat / Conditional Use / Site Plan-Design Review / Vacation /
        Annexation / Variance-Exception.
      - **Extend the recommendation-vs-final-action distinction (SLC's `action_class`)
        to all PC datasets**, derived from result/motion phrasing ("recommend approval"
        vs final approval) — key for technical-vs-political divergence analysis.
      - Audit sample: hand-verify ≥100 classified motions across cities before accepting.
- [x] **2.4 Body & vote-value crosswalks.** DONE 2026-07-02:
      `crosswalks/body_crosswalk.csv` (26 rows) from the actual body values in all CSVs
      + sandy's Legistar `body` table (10 bodies read from db/sandy.db) — RDA=
      Redevelopment Agency; SLC + nephi CRA both = Community Reinvestment Agency
      (verified from each city's docs); MBA=Municipal Building Authority except lehi
      (its docs name the separately-meeting body the Local Building Authority; repo
      code MBA kept verbatim); LBA/HA/SSLD; st_george ArtsCommission flagged as a
      different-people body and Canvass as the council-as-canvass-board.
      `crosswalks/vote_values.csv` (42 rows) documents each city's recorded value set
      and ceilings: orem Aye/Nay(+8 Abstain) only, Recuse in 8 cities, vineyard no
      Abstain, sandy `Excused` + db-only `Nonvoting`, park_city tie-break Nays carrying
      `vote.note` in its db, logan/nephi narrative no-name votes. Both emitted from
      tables embedded in `scripts/normalize_motions.py`. Original scope: `body_crosswalk.csv` (RDA ↔ Redevelopment
      Agency, MBA/HA/SSLD/CRA/LBA, PlanningCommission) with per-city notes; document each
      city's vote-value ceiling (orem = Aye/Nay only; who records Recuse/Abstain) in the
      spec so comparisons know what's comparable.
- [x] **2.5 SLC retrofit.** DONE 2026-07-02: dirs renamed (`public_comments/`,
      `election_results/`) + full reference sweep (scripts/docs/path-scoped skill; stale
      Desktop path fixed); `body` column added to council `all_votes.csv` (13-col standard,
      Council 10,528 / RDA 1,485 / CRA 556 / LBA 271; 0 unmatched, stripping it reproduces
      the old file byte-for-byte); `minutes_index.csv` migrated to the standard schema
      (457 rows 1:1; legacy extras frozen in `minutes_index_legacy.csv`; scrapers updated
      to emit/preserve it); `extract_votes.py` + `db/build_db.py` read/write the new
      column (db rebuild byte-identical: 2,582 motions · 18,157 votes · 31 referrals);
      weeks/ rebuilt byte-identical; recon.md (retrospective) + VERIFICATION.md written,
      README rewritten to template. Motion_type crosswalk NOT applied — awaits 2.3's
      crosswalk table. Details: slc VERIFICATION.md. (bring the template city into its own standard):
      `slc_public_comments/` → `public_comments/`, `municipal_election_results/` →
      `election_results/` (with path fixes in scripts/docs/skills that reference them);
      add `body` column to council `all_votes.csv` (recoverable — the db build already
      derives body per motion from section headers); regenerate `minutes_index.csv` in
      the standard schema; apply motion_type crosswalk; add `recon.md`; write
      `VERIFICATION.md`; rewrite README to the standard template. Keep original CSVs in
      `_backups/`.
- [x] **2.6 Sandy db conformance.** DONE 2026-07-02: sandy.db rebuilt on the standard
      schema (west_valley-template core from the two flat CSVs; full Legistar harvest
      preserved in `legistar_*` extension tables — 10 bodies / 2,825 matters / 10,443
      raw vote rows incl. `Nonvoting` + Board of Adjustment). **Council votes re-sourced
      minutes-primary** (measured: minutes 240 vote dates / 292 Nays vs Legistar 214 /
      173; Legistar omits narrative + some whole contested roll calls — decision +
      numbers in sandy `db/SCHEMA.md`); PC votes stay Legistar (only source), all 554
      motions mapped 1:1 to EventItems (`app_match_method='matter_id'` extension).
      Reconciliation exact: 8,120 CSV named rows = 8,109 votes + 11 documented
      `vote_overrides.csv` dup pairs (3 conflicts resolved explicitly, incl. the
      minutes' Sharkey double-listing). `name_key` NOT NULL UNIQUE restored
      (collision-free); standard CHECKs restored; referral layer rebuilt with the shared
      generalized template (116 links; 98/124 old links reproduce at MatterId grain,
      rest documented structural). Validator sandy exemption REMOVED —
      `validate_city.py`: 0 FAIL on all 13 cities; rebuilds byte-identical.
      Original scope: map the Legistar fork onto the standard schema (standard
      tables/columns, `Nonvoting` documented as extension; Legistar extras preserved in
      city-local columns/tables) so cross-city db queries behave.
- [x] **2.7 Federated view.** DONE 2026-07-02: `scripts/build_cities_db.py`
      (stdlib-only, idempotent) builds root `cities.db` — the 8 standard tables from
      all 13 dbs unioned with a `city` column, ids namespaced by per-city offsets
      (index×10M; FKs verified, 0 violations), park_city `vote.note` carried (NULL
      elsewhere), sandy `legistar_*` extensions excluded (stay in sandy.db). Row
      counts reconcile EXACTLY (asserted every build): 49 bodies / 452 persons /
      4,470 meetings / 7,780 applications / 23,110 motions / 111,944 votes / 563
      roles / 944 referrals (final build 20:24, absorbing the same-day
      st_george/provo extractor fixes). All 26 motions_std.csv loaded as `motion_std` and
      joined to `motion` on (source, motion_no, meeting_date) — **100.00%
      (23,110/23,110, 1:1)** incl. sandy PC's degenerate key. Crosswalks loaded as
      tables; 21-row `caveat` table (tally-only/dissent-only/vote-ceilings/coverage
      floors/body gaps/comments-two-cities/elections-2019-floor…); caveat-aware
      views `v_contested_all` / `v_member_record_all` / `v_landuse_outcomes` /
      `v_pc_divergence` (drops low-confidence links by design) / `v_coverage`.
      Docs: root `cities_db_SCHEMA.md` (namespacing, reconciliation, marquee
      queries) + README/CLAUDE.md sections. DERIVED — rebuild after any per-city
      db rebuild. Original scope: unioning the 13 dbs into
      `cities.db` with a `city` column; views for cross-city questions; documented
      caveats table (coverage asymmetries — comments in 2 cities, Nephi's tally-only
      votes, elections 2019+ outside SLC).
- [x] **2.8 Sources & citation index.** DONE 2026-07-02: `scripts/build_sources_index.py`
      (stdlib-only, idempotent) wrote sources.csv + SOURCES.md in all 13 cities — 6,937
      documents, 6,713 (97%) with a recorded direct URL — plus repo-root
      `sources_summary.md` (city×dataset coverage + liveness). URLs never invented:
      unrecorded provenance carries the issuing office (all elections except
      orem/nephi/park_city partials; SLC's 68 Laserfiche minutes; sandy PC API export).
      Liveness sample 5/city: 64/65 live, 0 rotted hosts (ogdencity.gov merely 404s
      non-browser UAs; probe retries). Flagged: 26 vineyard minutes_index URLs recorded
      without the required `,plainText=` arg → 404 as written (defect, not rot).
      `--verify-sample` stamps verified_date; stamps survive rebuilds. Per-city machine-readable `sources.csv` (every
      document: dataset, record key, local path, source_url, retrieval/verified dates,
      extraction method, processing-chain reference) generated by
      `scripts/build_sources_index.py` from the existing heterogeneous provenance
      (minutes_index.csv, comment manifests, election docs, expansion index.csv files),
      plus a human-readable, citation-ready `SOURCES.md` per city for web sharing.
      Rationale: raw PDFs may not be retainable long-term (disk); the URL index is the
      recovery path and the public reference layer.

## Phase 3 — Harden (methodology & reproducibility)

- [x] **3.1 Validation everywhere.** DONE 2026-07-02: one shared council-vote validator
      (`scripts/validate_votes_template.py` — schema/dates/vocab, names_recorded motion
      convention, double-vote check honoring documented exceptions, roster resolvability
      (observed-roster fallback), result-tally vs counted rows using motions_std parsed
      tallies) installed as `meeting_minutes/validate_votes.py` in the 10 cities lacking
      one (config block only, no forked logic; lehi/ogden/vineyard keep their bespoke
      validators — shared checks run against them too). Run in all 13: **0 hard failures
      and 0 unexplained tally mismatches everywhere**; every residual flag is a
      hand-verified, config-documented source quirk (per-city one-liners in each
      VERIFICATION.md). Wired into `validate_city.py` as check j (presence + clean run).
      **Same pass fixed the 15 duplicate (source,motion_no,date,member) rows left from
      2.1:** 3 were extractor artifacts, fixed + re-extracted (slc PC McCall→Mike
      Christensen surname collapse — also recovered 10 silently-dropped McCall votes;
      nephi PC roll-call scan reading past the outcome declaration); 12 were faithful
      source clerk contradictions, kept verbatim in the CSVs and resolved in the dbs via
      the park_city `db/vote_overrides.csv` pattern (fail-loud build) now extended to
      ogden/st_george/provo/west_jordan/slc. Validator h.db reconciles exactly in all 13
      cities (sandy via its 2.6-conformant db + its own vote_overrides.csv, landed
      concurrently). Also done in this pass:
      slc PC `minutes_index.csv` migrated to the standard schema (145 rows 1:1, legacy
      frozen, extractor updated) and the stale `st_george .../CLAUDE 2.md` removed.
      Original scope: `validate_votes.py` for council votes in all 13
      cities (exists in 3); run in-place; wire into `validate_city.py`.
- [~] **3.2 Raw retention policy.** SPLIT 2026-07-02: the go-forward retention rule is
      DONE (encoded in the build + audit skills, 3.6/expansion contract). The
      **backfill of discarded raw PDFs is DEFERRED by owner decision (disk space)** —
      moved to `TODO.md` along with the proposed Wayback-archiving alternative. The
      citation index (2.8, sources.csv per city) is the recovery path meanwhile.
- [x] **3.3 Refresh paths.** DONE 2026-07-02: `fetch_new.py` in all 13 cities (shared
      plumbing in `scripts/refresh_lib.py` — index-max baseline, ≥1s-throttled
      research-UA HTTP, raw/ retention, index-append + `fetch_log.csv` retrieved_date
      provenance, `refresh_probe.json`, common `--probe`/`--fetch` CLI; vendor logic
      per city: PrimeGov slc+wj, Granicus lehi, Legistar sandy, CivicClerk
      park_city+vineyard, CivicClerk+GDrive orem (keyless `embeddedfolderview`
      listing works), OnBase provo+wvc, CivicPlus nephi+ogden(+provo PC), Revize
      logan+st_george, slcdocs slc-PC; slc comments **wrap** check_new_comments.py,
      not duplicated). Covers meeting_minutes + planning_commission everywhere
      (+ slc public_comments). **All 27 dataset probes run live 2026-07-02:
      0 endpoint failures**; 12 new docs available repo-wide (park_city 2, orem 2,
      sandy 3 council + 1 PC event, wvc 2, wj 1, provo-PC 1) — probe-only by design,
      nothing ingested this pass. Notable: lehi's 5-month council staleness is
      city-side (19 meetings listed on Granicus, minutes unposted since 01-27).
      `scripts/refresh_status.py` → repo-root `refresh_status.md` (city×dataset:
      index max, probe date/result, new-count, fetch cmd; quarterly routine
      documented there). Each city CLAUDE.md gained a "Refreshing" section
      (originals in `_backups/2026-07-02/*/CLAUDE.md.pre-3.3`). Original scope:
      Per-city `fetch_new.py` (portal-vendor-specific, modeled on
      SLC's `check_new_comments.py`) + a repo-level `refresh_status.md` showing each
      city's as-of date; document a quarterly refresh routine.
- [x] **3.4 Environment & paths.** DONE 2026-07-02: `requirements.txt` from an actual
      import inventory (7 third-party pkgs — anthropic/pypdfium2/pillow/markdownify are
      SLC-pipeline-only, geopandas/shapely geo-only, requests skill-only; core pipeline
      confirmed stdlib-only; all verified installed, versions pinned as floors) +
      `SETUP.md` (python 3.11, brew poppler/tesseract, the two SLC `.env` key files,
      validator + regeneration entrypoints). Desktop sweep: fixed 5 live scripts still
      pointing at `~/Desktop/<city>...` (provo extract_comments.py + 2 fetch .sh,
      st_george extract_comments.py + build_clean_csv.py — all now __file__-relative),
      2 doc footers (st_george VERIFICATION, vineyard dossier), and normalized orem's
      absolute-Desktop `source_file` paths to repo-relative in 12 CSVs (95+95+121+4 rows,
      all targets verified on disk; VERIFICATION addendum added). The two shared election
      archives verified still at `~/Desktop/` (intentional — annotated in wvc geo script,
      SETUP.md, and the build skill). Remaining Desktop refs are historical recon/
      VERIFICATION records or valid archive pointers. Stale skill `templates/__pycache__`
      removed. SLC 2.5 path fixes re-verified clean. Originals in `_backups/2026-07-02/`.
- [x] **3.5 Extractor convergence.** DONE 2026-07-02: `scripts/vote_extract_lib.py`
      (stdlib-only) — the mandatory skeleton for NEW cities (existing 13 NOT migrated;
      they migrate only when touched): minutes-tree walker, provenance-header stripper,
      case-sensitive roll-call label helper (park_city fabricated-Recuse lesson),
      full-name-first `NameMatcher` (slc Christensen lesson; shared surnames never
      guessed), `truncate_at_outcome` (nephi declaration-scan lesson), 13-col CSV +
      per-meeting JSON writers, `basic_checks()` pre-write gate + validate_votes/
      validate_city hooks; smoke-tested on real corpora (reproduces park_city's 9
      documented contradictions exactly); concrete pointer added to the build skill's
      extraction_standards.md. **Same pass fixed the 3 logged extractor defects**
      (each: backup → minimal class-wide fix in the city's own extractor → regenerate →
      row-level diff → db+weeks rebuild → validators 0 FAIL → VERIFICATION updated):
      st_george PC 2025-02-25 m1/m2 role-prefix-run fix (+6 Aye rows, results 2:0→5:0;
      corpus sweep: only those lines affected; 2 separate pre-existing gaps newly
      logged); provo inverted-cue "Opposed were …" (+3 Nay 2022-11-01 m5, +4 Nay
      2022-12-13 m10 — the class's only 2 corpus instances); west_jordan "made a
      second/substitute motion" anchor + tie→Fail vocabulary (2023-12-20 m7 now 3-3
      Fail + new tally-only m8 5-1 Pass; 5 verified substitute-motion siblings gained
      mover/clean text). **And the Ogden agenda-subject re-extraction** (2.3's honest
      residual): 500/501 bare adoption motions enriched with verbatim `[ENTITLED:
      "…"]`/`[AGENDA ITEM: "…"]` long-titles matched by instrument number (1 honest
      miss: source number mismatch); all 500 verified verbatim substrings of source;
      old motion text a strict prefix of new in every changed row; 208 reclassify
      (74 Land-Use, 96 Budget, 14 Interlocal, …) — ogden Land-Use 9.3%→13.4% (council
      1.5%→6.9%), 284 remain genuinely non-land-use ordinances; referrals 1→4 (id-pins
      re-bound, 4 new false-positive links suppressed & documented). cities.db +
      coverage.json + sources index rebuilt; validate_city sweep: **0 FAIL on all 13**.
      Details: st_george/provo/west_jordan/ogden VERIFICATION.md 3.5 addenda +
      crosswalks/README.md (ogden paragraph rewritten).
- [x] **3.6 Skill updates.** DONE 2026-07-02 (full skill backed up to
      `_backups/2026-07-02/build-city-data-repo-skill/`). SKILL.md: PC promoted to a
      core Phase-2 dataset (own acquisition agent, same standards); new "second
      non-negotiable: RAW RETENTION" section (WJ packet loss + 11-cities-no-raw cited;
      old delete-after-extract guidance explicitly superseded); mandatory post-extraction
      screen_corpus.py gate with per-year checks + pathology catalog (PUA fonts, bad OCR
      layers, source-side wrong-doc uploads → duplicate-body + date-vs-content checks);
      Phase 4 now db+weeks+normalize_motions/crosswalks; Phase 5 adds the
      SCHEMA_SPEC/validate_city.py 0-FAIL conformance gate; Phase 6 requires fetch_new.py
      (probe-newer-than-max(date) pattern) and `/audit-city-data` before done; base path
      `~/civic-data/`, election archives noted as intentionally-Desktop.
      extraction_standards.md: gate section + validate_votes.py spec for BOTH bodies
      (modeled on lehi/ogden/vineyard) + agenda-subject capture (Ogden 428), case-
      sensitive result regexes (Park City fabricated Recuse), roster-vs-attendance
      completeness (Sandy Scott Earl), motions_std/crosswalk pointer.
      verification_standards.md: screener re-run + validate_votes checks + conformance
      gate + audit-as-final-deliverable. repo_structure.md: normative-spec pointer,
      standard index schema + minutes_unrecovered, motions_std, VERIFICATION/fetch_new
      requirements. planning_commission_playbook.md: reframed core-not-bolt-on, pure-
      deterministic-extractor rule. recon_agent_brief.md: PC recon item added.
      election_playbook.md: archive-location note. templates/CLAUDE.md.tmpl: rewritten to
      the standard (index/vote schemas, PC + db + motions_std, recon/VERIFICATION
      expectations, fetch_new). lessons_learned.md: dated 2026-07-02 fleet-audit entry +
      supersession note on the old disk-discipline section. Election-archive logic
      untouched beyond path notes.

## Sequencing

1. Phase 1 items are independent → run in parallel (per-city agents).
2. Phase 2.1–2.4 next (spec + crosswalks), then 2.5 SLC retrofit, then 2.6–2.7.
3. Phase 3 last; 3.2 backfill can run in the background anytime after Phase 1.
