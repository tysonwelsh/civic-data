# Repo-wide extraction & consistency audit — 2026-07-02

Six parallel agents: four PDF/extraction auditors (all 13 cities), one cross-city schema
review, one pipeline/methodology review. Ground truth: ~50 source PDFs (retained or
re-fetched via `minutes_index.csv` source_url) token-diffed or visually compared against
repo text; ~100 vote motions spot-checked; derived layers (db/, weeks/) reconciled
against flat CSVs. Method now encoded in `.claude/skills/audit-city-data/`.

## Headline

The extraction layer is overwhelmingly faithful — **the repo's real problems are two
localized failures (Sandy 2021–23, Ogden 2022), a handful of file-level defects, and
drift in the derived/documentation layers — not the feared systemic PDF garbling.**
OCR- and vision-derived text preserves source typos verbatim (strong anti-hallucination
evidence); no invented text was found anywhere.

## Grade summary (city × dataset)

| City | Council minutes | Council votes | PC minutes/votes | Public comments | Notes |
|---|---|---|---|---|---|
| slc | A (2021+), B (2020 OCR) | A (LLM-extracted, spot-verified) | A− | A− (vision, 13,334 rows) | doc drift: README "scaffold only" stale; counts stale |
| st_george | A− (2025-10-09 = copy of 10-16) | A− (~110 misdated dup rows) | A− | A (incl. verified vision rows) | cleanest large city otherwise |
| west_valley | A | A | A | A (honest empty) | "raw/ retained" doc claim false |
| provo | A (0.998–1.000 sims) | A | A− (2025+ only, source limit) | **B — 10–15% of letters truncated mid-page** | |
| lehi | A (1.000 recall) | A | A | A | |
| logan | A | A | A/B (52 OCR files) | A (honest empty) | 1 split-boundary line loss (RDA 2026-05-12) |
| nephi | A | A (but only 259 named rows — source limit) | B (1 garbled file 2024-01-10) | A (honest empty) | |
| orem | A (text) / B (68 OCR) | A | A | A | Aye/Nay only — no absences captured |
| park_city | A | **B — 9 contradictory dup rows, 1 spurious motion** | A | A (459 rows) | **db drops 11 rows incl. BOTH mayor tie-breaks; weeks/ stale (0 comments shown vs 459)** |
| west_jordan | A− | A− | B (OCR junk, tally-only) | B+ (1 near-dup missed) | |
| vineyard | **B — 2 stub files, 2020-06-24 is wrong doc (=Feb 26 copy)** | **B — ~71 dup rows** | B+ (1 dup meeting) | A (honest empty) | 29 raw packets retained (2.5 GB) |
| ogden | **C — 2022 garbled OCR + ≥8 uncarved meetings** | **C — 2022: 47% of roll calls undercaptured** | B+ | A (honest empty) | docs blame 2023; it's 2022. Raw compilations retained |
| sandy | **C — 63/274 files (23%) PUA font-garbled (2021–23)** | **C — ~190 motions / 121 roll calls missing entirely** | B (Legistar API; phantom `minutes/` doc claim) | A (honest empty) | raw PDFs retained; garbling mechanically reversible (−0xF000) |

## Confirmed defects (ranked by severity)

### Data loss / garbling
1. **Sandy PUA garbling** — 63/274 council minutes majority-encoded U+F0xx (broken font
   cmap, faithfully copied from the source PDFs). Extractor got **zero votes** from them:
   2022 shows 15 voting meetings, 2023 shows 7 (vs ~40 normal). Decoding = subtract 0xF000.
   Raw PDFs on disk. Also: 16 documented motions with page-break-dropped Aye lists.
2. **Ogden 2022** — compilation PDF's embedded OCR layer used as-is (stray-space rate
   226/10k tokens vs 4–6 other years); ≥8 meeting dates in `raw/minutes/compilation_CC_2022.pdf`
   never carved (index has 30 dates vs 42–45 other years); 47% of 2022 roll calls captured
   ≤5 of 7 voters (names split like `C l-IO BERKA`). Docs say coverage complete and blame 2023.
3. **Vineyard wrong/missing docs** — `2020-06-24_…regular.md` is a byte-copy of the
   2020-02-26 minutes (June 24 silently missing; Feb 26 votes double-counted); 2 header-only
   stubs (2020-09-23, 2023-08-30) indexed as real minutes; 2024-04-10 combined doc parsed
   twice; PC 2023-06-21 = copy of 06-07. Net ~81 duplicate vote rows.
4. **Provo comment truncation** — page-containment cut chops multi-page letters
   mid-sentence; ~8–12 of 81 rows. Verified vs `raw/packet_txt/`. Docs claim lossless containment.
5. **St George wrong doc under 2025-10-09** (found post-audit by the generic
   duplicate-bodies screen in `.claude/skills/audit-city-data/`): `minutes/2025/2025-10-06/
   2025-10-09_city-council-work-meeting.md` is a byte-identical copy of the 2025-10-16
   regular-meeting minutes. The real Oct 9 work-meeting minutes are missing, and
   `all_votes.csv` carries 110 rows dated 2025-10-09 extracted from Oct 16's minutes
   (Oct 16 itself has 70) — duplicated/misdated votes. Same class as the Vineyard defect;
   demotes St George council minutes A → A−.
6. **Nephi PC 2024-01-10** — 167 U+FFFD ("ti" ligature loss from defective source font;
   present in source PDF; vision re-read recoverable). **Logan RDA 2026-05-12** — final
   line lost at council/RDA split boundary.

### Derived-layer integrity
6. **Park City db** — `(motion_id, person_id)` UNIQUE silently drops 11 vote rows,
   arbitrarily resolving 9 contradictory Aye+Nay pairs and deleting **both mayoral
   tie-break votes** (Beerman 2020-06-25, Worel 2024-08-22) from the "canonical" layer;
   docs claim exactly 1 tie-break (data has 2). One spurious motion whose `result` is an
   Orlando URL. Referral counts: db 100 vs docs 99.
7. **Park City weeks/ stale** — built 31 min before comments finalized; all 202 summaries
   say "Public comments: 0" vs 459 real. Fix: rerun `build_weeks.py`.
8. **db not built at all** for lehi, park_city†, sandy (`build_db.py` present, db missing
   or fork). †park_city has parkcity.db but see #6.

### Cross-city standardization (from schema review)
9. **`result` column has no controlled vocabulary** — 8–33 distinct free-text strings per
   city (`4-0 Pass` / `4:0 Pass` / `Carried unanimously` / `Voice Pass` / `Died (no second)` /
   st_george's embedded prose / park_city's URL). Worst single threat to cross-city comparison.
10. **SLC (the template) is the standard's biggest non-conformer**: no `body` column in
    council votes, different `motion_type` labels for 7 shared concepts (+`Legislative
    Intent` SLC-only), different `minutes_index.csv` schema, `slc_public_comments/` +
    `municipal_election_results/` dir names, no recon.md/VERIFICATION.md.
11. **Sandy db is a schema fork** (Legistar): different meeting/application/motion columns,
    `Nonvoting` vote value, dropped CHECK constraints, 10 bodies.
12. **Body naming inconsistent**: SLC spells out (`Redevelopment Agency`), clones use
    acronyms (`RDA/CRA/MBA/HA/SSLD`); needs a crosswalk table.
13. **Vote-value sets differ**: `Recuse` in 7 cities only; `Abstain` absent in 3; orem
    records Aye/Nay only; park_city free-text `Nay (Mayor tie-break)`.
14. **Coverage asymmetry**: public comments substantive in only slc (13,334) + park_city
    (459); 6 cities honestly zero (not published); 4 cities single-year slivers. Nephi
    named votes near-empty (259) — source limitation. Elections: SLC 2007–2025, others 2019+.

### Methodology / reproducibility (from pipeline review)
15. **Raw minutes PDFs discarded in 11/13 cities** (Sandy, partial Vineyard/Ogden are the
    exceptions). Recovery depends entirely on `source_url` liveness (all sampled URLs
    resolved 2026-07). West Jordan comment packets were already lost once (re-fetched into
    `_audits/comment_qc/`).
16. **`extract_votes.py` is 13 unrelated hand-written parsers** (191–1,036 lines, 0–44
    regexes); PC extractors likewise; no shared template. Council-vote validation script
    exists in only 3/13 cities. By contrast `build_db.py`/`build_weeks.py`/`build_referrals.py`
    are disciplined single templates (11/13 byte-identical).
17. **Only SLC has an incremental refresh path** (`check-slc-comments` skill +
    check_new_comments.py). 8 cities have no fetch scripts at all — one-shot snapshots.
18. **No env manifest** (no requirements.txt); hardcoded `~/Desktop/...` paths in SLC
    skill/docs and the build-city-data-repo skill (repo now lives at `~/civic-data`);
    stale artifacts (`extract_votes 2.py`, orphan .pyc).
19. **Machine-readable provenance is partial**: `source_url` in minutes_index.csv (good;
    SLC only 389/457) but no extraction date/method per file; comment provenance schemas
    differ per city; no repo-root README, manifest, or shared vocab spec; skill-mandated
    repo-root VERIFICATION.md never produced.

### Doc drift (docs contradicting data)
- Ogden: "2023 is OCR" → actually 2022; "coverage complete" → false for 2022.
- Park City: tie-break count (1 vs 2), motion count (1,562 vs 1,567), referrals (99 vs 100).
- West Valley: "immutable original PDFs in raw/" → dirs empty; speaker log 819 vs 818.
- Vineyard: meeting counts 138/165/173 in three places; defects absent from VERIFICATION.md.
- Sandy: PC CLAUDE.md claims `minutes/` dir + index files that don't exist.
- SLC: README calls meeting_minutes "scaffold only"; comment count 12,887 vs 13,334.
- Nephi: "227 PDF + 16 docx" vs index marking all 243 `format=text`.
- West Jordan: "no OCR" — PC is 36/84 OCR; council has OCR'd signature pages.

## Verified-clean highlights
- 21/21 and 11/11 re-fetched source PDFs diffed at 0.998–1.000 similarity (lehi, logan,
  nephi, orem, park_city, west_valley, provo, slc-PC).
- SLC vision comments: page-level verification exact in 3 eras incl. multi-page stitching;
  form-letter "duplicates" confirmed real in source; ~8 unrecoverable pages documented.
- OCR corpora preserve source typos (`Sherriff Tower`, `Mr. Summer`) — no LLM rewriting.
- St George and West Valley pass every check materially; election results verified
  against retained canvass PDFs to the vote.

## Remediation addendum — Phase 1.9 follow-up (2026-07-02): duplicate-body screen, 4 cities

A repo-wide re-run of the generic duplicate-bodies screen found **12 identical-body file
groups the original audit missed** (same class as defects #3/#5). All verified at source
before touching anything; all repaired the same day. Originals in `_backups/2026-07-02/`.
Per-city detail in each city's VERIFICATION.md (2026-07-02 addenda).

- **Lehi (8 pairs — 6 council, 2 PC):** one minutes doc attached to TWO consecutive Granicus
  events (Pre/Regular, Oath/Regular, PC work/regular) — all 16 source doc_ids re-fetched,
  each pair md5-identical, each pair distinct from the others. One file per pair removed
  (kept the event matching the doc's self-description). The 2024-06-18 clip673/698 pair is
  two REAL meetings — untouched. Council votes 6,412→6,147 (−265), PC 6,269→6,219 (−54);
  surviving rows byte-identical; db 2,405→2,342 motions / 12,681→12,362 votes; referrals
  474→459 (net 1 lost + 2 gained after twin-normalization, all traced to duplicate apps
  deflating the linker's IDF weights — no overrides exist, no remap needed); weeks 165.
  Knock-on: ordinances/index.csv 18 source refs remapped to kept twins; speaker log 160→148
  (−12 dup paraphrases); pmn coverage counts updated. Screener: duplicate_bodies 0/175, 0/160.
- **Nephi (wrong-date):** 2021-02-23 file was a city-side mis-upload of the 02-16 minutes
  (AgendaCenter serves the same text under both dates — verified). Real 02-23 work-session
  minutes RECOVERED from PMN notice 661433 (files/691883.docx), converted per corpus
  conventions. Votes 1,094→1,090 (−5 wrong dup rows, +1 real motion); referrals 18→18
  link-for-link; screener 0/243.
- **Orem (wrong-date, PC):** 2025-10-15 file was CivicClerk fileId=1005, byte-identical to
  the 2025-11-05 minutes (fileId=1006) — mis-upload at source; real Oct-15 minutes NOT
  published anywhere found (PMN notice 1027529 has agenda/packet/resolutions only). Removed +
  logged in minutes_unrecovered.csv. Both files parsed tally-only → all_votes.csv
  byte-identical (0 row delta); motions 567→562; db/referrals byte-identical; screener 0/114.
- **West Jordan (same-date, two names):** 2022-06-22 council meeting parsed twice
  (PrimeGov published one PDF under two meeting templates — both URLs fetched, byte-identical).
  Kept the file matching the doc's self-title ("CITY COUNCIL MEETING"); votes 6,783→6,705
  (−78); db 1,175→1,163 motions; referrals 21→21 link-for-link; screener 0/321.

Screeners re-run post-repair on all four corpora: **duplicate_bodies = 0 everywhere**; the
only intentionally retained same-date pair (Lehi 2024-06-18) has distinct bodies and does
not flag. All other-city corpora were unaffected by this follow-up.
