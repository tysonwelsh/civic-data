# VERIFICATION — SLC City Council data repository

SLC was the original, pre-template city, so unlike its 12 clones it had no build-time
VERIFICATION.md. This file (created 2026-07-02) records (1) the independent repo-wide
audit's findings for SLC and (2) the Phase 2.5 standardization retrofit and its checks.
Full audit: `_audits/2026-07-02/report.md`. Plan: `REMEDIATION_PLAN.md` (Phase 2.5).

## 1. Audit 2026-07-02 — SLC grades & findings

| Dataset | Grade | Notes |
|---|---|---|
| Council minutes | **A** (2021+ PrimeGov Markdown), **B** (2020 Laserfiche OCR) | OCR preserves source typos verbatim (anti-hallucination evidence) |
| Council votes | **A** | LLM-extracted, spot-verified against minutes |
| PC minutes/votes | **A−** | pure-regex extraction; re-fetched source PDFs diffed 0.998–1.000 |
| Public comments | **A−** | vision-extracted, 13,334 rows; page-level verification exact in 3 eras incl. multi-page stitching; ~8 unrecoverable pages documented |

- No invented text found; form-letter "duplicates" confirmed real in the source PDFs.
- **Doc drift (fixed in Phase 1.8, 2026-07-02):** README called `meeting_minutes/`
  "scaffold only" (it holds 457 docs / 12,840 vote rows); comment counts stale
  (12,887 → measured 13,334); PC recommendation/final-action split re-measured
  (252 recs = 211 pos / 41 neg · 290 final actions · 198 procedural).
- **Standardization findings (audit item 10):** SLC — the template city — was the
  standard's biggest non-conformer: no `body` column in the council votes CSV, a
  nonstandard `minutes_index.csv` schema, nonstandard directory names
  (`slc_public_comments/`, `municipal_election_results/`), no recon.md/VERIFICATION.md,
  stale hardcoded `~/Desktop/...` paths in the refresh skill, and spelled-out body
  names where clones use acronyms.

## 2. Phase 2.5 retrofit — 2026-07-02 (this change)

Goal: bring SLC into the standard its clones follow, changing **no data content**
except where specified. Originals of every modified file are in
`_backups/2026-07-02/slc_city_council/`.

### Changes
- **Directory renames:** `slc_public_comments/` → `public_comments/`;
  `municipal_election_results/` → `election_results/`. All path references in scripts,
  docs, and the path-scoped `check-slc-comments` skill updated; the skill's stale
  `~/Desktop/slc_city_council/...` path fixed to `~/civic-data/slc_city_council/...`.
- **`body` column added** to `meeting_minutes/all_votes.csv` (12 → standard 13 columns,
  `body` after `title`; clone-standard short vocabulary Council/RDA/CRA/LBA). Values
  derived from `db/civic.db`, whose build walks the source minutes' section headers —
  joined on the exact key (source file, motion_no).
- **`minutes_index.csv` regenerated** in the clone-standard schema
  `date,year,title,slug,path,source,source_url,format` (primegov→`text`,
  laserfiche→`ocr`). The old index (extra `week_start`/`chars`/`ref_id` columns) is
  frozen as `meeting_minutes/minutes_index_legacy.csv`; `scrape_primegov.py`'s
  `rebuild_index()` now emits the standard schema (and carries provenance over on
  partial re-runs); `scrape_laserfiche.py` now writes its rich per-page index to
  `index_laserfiche.csv` instead of clobbering the standard file.
- **`db/build_db.py`** now reads the CSV's `body` column (short codes mapped back to
  the db's full body names); its markdown section-walk remains as the derivation of
  record / fallback for a body-less CSV.
- **Docs:** README rewritten to the clone template; `recon.md` (retrospective) and this
  file created; CLAUDE.md path references updated.

### Verification results (all 2026-07-02)
- **all_votes.csv:** row count unchanged (**12,840**); `body` populated **100%**
  (0 unmatched rows); stripping the new column reproduces the pre-change file
  **byte-for-byte** (no other cell touched). Distribution: **Council 10,528 · RDA
  1,485 · CRA 556 · LBA 271** — consistent with the db's per-body motion counts
  (Council 1,510 · RDA 213 · CRA 80 · LBA 39 ≈ 7 votes/motion in each body).
- **db rebuild** (`db/build_db.py` + `db/build_referrals.py`) from the 13-col CSV:
  `civic.db` and every `db/tables/*.csv` **byte-identical** to the pre-retrofit build —
  5 bodies · 70 persons · 494 meetings · 893 applications · 2,582 motions ·
  **18,157 votes** · 31 referrals (11 high / 15 medium / 5 low) · INTEGRITY OK.
- **weeks/:** `build_weeks.py` re-run after the renames — all 327 bundles (1,255 files)
  **byte-identical** to before. Re-run again after the body-column addition: exactly the
  166 weekly `votes.csv` files changed (they now carry the `body` column, matching the
  canonical CSV row-for-row); every summary/comments/minutes/index file byte-identical.
- **minutes_index.csv:** 457 rows preserved 1:1; 389 `source_url` populated / 68 blank
  (2020 Laserfiche — honestly blank, per-doc provenance in `index_laserfiche.csv`);
  format = 389 text / 68 ocr; every `path` exists on disk; `rebuild_index({})`
  regenerates the migrated file byte-identically.
- **Reference sweep:** repo-wide grep for `slc_public_comments|municipal_election_results`
  clean outside `_audits/`, `_backups/`, and `REMEDIATION_PLAN.md` (historical records,
  intentionally untouched). All SLC scripts compile; `check-slc-comments` skill paths
  all exist.

## 2026-07-02 addendum — duplicate member-vote adjudication (plan item 3.1 prep)

The repo validator flagged 6 duplicate `(source, motion_no, date, member)` pairs in
`planning_commission/all_votes.csv`. Each was adjudicated against the source minutes:

- **2 extractor artifacts (fixed):** PC 2024-10-23 m2 and 2024-11-13 m3 — the minutes
  name **McCall Christensen** (seated 2024-10→2025-08) but the extractor's
  surname-only vote-list scan resolved "Christensen" through a one-entry surname map,
  misattributing McCall's votes to **Mike Christensen** (producing a false Aye+Nay pair
  for Mike). `extract_votes.py` now matches exact full names first (whitespace-tolerant)
  and only then falls back to bare surnames (`surname_scan`/`map_one`). Re-extraction
  verified end-to-end: with the old code a full `--force` rebuild reproduced the old CSV
  byte-identically; with the fix, exactly the affected meetings changed. **Bonus
  recovery:** the same collapse had been silently *dropping* McCall's votes wherever both
  Christensens were listed — 10 genuinely-recorded votes recovered (2024-10-23 m1/m3/m4,
  2024-11-13 m1/m2/m4/m5/m6, 2025-01-08 m1/m2; each verified against the printed Yes/No
  lists). PC rows 5,323 → 5,333; roster unchanged; result tallies for those motions
  re-derived (e.g. `6:0` → `7:0`), and `motions_std.csv` regenerated.
- **4 faithful source contradictions (kept in CSV, resolved in db):** PC 2025-03-26 m1,
  2025-04-23 m1, 2025-07-23 m1 (Amy Barry Aye+Nay) and 2025-06-11 m1 (Lilah Rosenfield
  Aye+Abstain) — all compound consent agendas where the clerk deliberately recorded a
  SPLIT vote ("Yes: … Barry (minutes) / No: Barry (Design Review)"; "Abstain: Rosenfield
  abstained from the minutes"). The CSV keeps both verbatim rows; the db's single-vote
  grain resolves each via the new **`db/vote_overrides.csv`** (Barry→Nay ×3: the recorded
  dissent on the substantive item; Rosenfield→Abstain: park_city partial-abstention
  precedent), applied fail-loud by `db/build_db.py`.

db rebuilt: 2,582 motions · **18,169** votes (= 18,173 named CSV rows − 4 override
merges); referrals unchanged (31). Validator h.db: PASS ("reconciles exactly … + 4
documented overrides"). Note 2025-07-23 m1's Yes list prints "Christensen" twice, but
McCall is recorded absent that day — left as a single Mike Christensen Aye (no
fabrication).

## 2026-07-02 addendum — PC minutes_index migration (Phase 2.5 leftover, done in 3.1)

`planning_commission/minutes_index.csv` migrated from the legacy header
(`source,year,week_start,meeting_date,title,source_url,format,file`) to the standard
`date,year,title,slug,path,source,source_url,format` — same recipe as the council index:
**145 rows preserved 1:1** (slug derived from the filename; `path` keeps the
city-root-relative value matching `all_votes.csv` `source`), legacy file frozen verbatim
as `minutes_index_legacy.csv`, and `extract_votes.py` (`read_index`/`process`) updated to
consume the standard schema going forward (week bucket derived from the path layout;
legacy header still tolerated). Verified: every `path` exists on disk, all dates parse,
sources slcdocs 106 / laserfiche 32 / slc.gov 7 carried over unchanged; a full
`extract_votes.py` pass under the new index resolves all 145 meetings and `--build-only`
reproduces `all_votes.csv` exactly (5,333 rows). Validator d.index[planning_commission]:
PASS (standard header; 145 paths exist; dates plausible).

**2026-07-02 (3.1) council-vote validation:** shared validator installed as `meeting_minutes/validate_votes.py` and run — 12,840 rows / 1,842 motions (all named); 0 schema/date/vocab defects, 0 malformed groups, 0 double votes; tally-vs-counted 1,842/1,842; 0 unexplained mismatches.
