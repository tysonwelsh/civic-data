# campaign_finance — Holladay City candidate financial disclosures (ACQUISITION-ONLY)

Municipal campaign-finance filings for Holladay City council/mayor candidates, added by
`/expand-city-sources` (source 6). **Additive, acquisition-only:** raw PDFs retained verbatim with
full provenance; **no dollar extraction, no OCR/vision, no totals** (`extraction_method` is `none
(acquisition-only; …)` on every row). Read `AVAILABILITY.md` for coverage, gaps, and discrepancy
flags before any quantitative claim.

## What's here

```
raw/                 52 filings verbatim + _fetch_log.jsonl (url, status, bytes, sha256, retrieved_utc)
index.csv            §9 campaign_finance contract header + documented city extensions
AVAILABILITY.md      per-cycle/candidate coverage vs holladay_races.csv, honest gaps, FLAGS, as-of
_disc/               discovery working dir (saved source HTML + batch list + its own fetch log)
holladay_cf_buildbatch.py   builds _disc/batch.csv (download list) from the saved discovery HTML
holladay_cf_buildindex.py   builds index.csv from raw/ + the fetch log (idempotent; re-runnable)
```

**52 files = 40 campaign-finance reports + 12 Conflict-of-Interest (COI) disclosures.** The COI
forms ("Elected Officer Annual Conflict of Interest Disclosure Statement", FY2025 + FY2026) are
**officeholder ethics disclosures, NOT campaign contribution/expenditure reports** — they carry
`filing_type='coi_disclosure'` and **must be excluded from any cycle or money total.** They were
captured because they sit on the same city disclosure page.

## Sources (see AVAILABILITY.md for the full search order)

- **City page** (`source=city_cf_page`): `holladayut.gov/departments/city_recorder/elections/
  disclosure.php` (Revize Document Center) — hosts the **2023 + 2025** campaign reports and the
  FY2025/FY2026 COI forms.
- **State tree** (`source=state_lg_municipal_disclosures`): `disclosures.utah.gov/Municipal` →
  `salt lake_2021_Holladay City` (7 files) and `salt lake_2017_Holladay` (4, bonus). The `_2023_`
  and `_2025_` state entries just redirect back to the city page.
- **SLCo Clerk**: non-municipal (county/school/township/state only) — verified, not a source.
- **2019**: state folder registered but **empty** (0 files); no 2019 filings exist — aligns with the
  known 2019 election-record gap (see flag 4 in AVAILABILITY.md).

## index.csv columns

§9 contract header first — `date, candidate, office, election_year, filing_type, reporting_period,
title, source_url, retrieved_date, format, extraction_method, path` — then documented city
extensions: `district, source, is_incremental, date_precision, in_election_results,
matched_election_candidate, join_confidence, sha256`.

- **`filing_type`**: `interim` (pre-primary/pre-general), `summary` (year-end Final), `statement`
  (period not stated), `coi_disclosure` (the 12 ethics forms — not campaign finance).
- **`format`**: `text` (13 born-digital) / `scanned` (39 image-only). No text sidecars are written
  (acquisition layer); the 39 scanned forms need OCR / `cf-vision-transcribe` to yield dollars.
- **`date` + `date_precision`**: `date` is the filing/reporting-period date; `date_precision`
  records how it was derived (`label_date`/`label_month`/`label_period` from the source label or
  filename, `inferred_pre_general`/`inferred_final`/`cycle_inferred` where only the cycle/period was
  known, `inferred_annual_deadline` for COI). Dates are best-effort — the source rarely prints an
  unambiguous filing date on the scanned forms.
- **`is_incremental='no'`** on campaign rows — the "FINANCIAL DECLARATION OF CANDIDATE" form is
  **cumulative-to-date**; NEVER sum a candidate's filings (double-count trap, SKILL §6). Blank for COI.
- **`in_election_results` / `matched_election_candidate` / `join_confidence`**: `yes`/exact where the
  candidate is a winner or runner-up in `election_results/holladay_races.csv` (names UPPER-CASE).
  `no`/none for Zac Wilson (un-named 2025 mayoral-primary 3rd) and Emily Gray 2023 D5 (uncontested,
  omitted from the SOVC) — both explained in AVAILABILITY.md, NOT coverage gaps.

## Rebuild

```
python3 holladay_cf_buildbatch.py   # (re)generate _disc/batch.csv from saved discovery HTML
                                     # then: polite_fetch.py --batch _disc/batch.csv --out raw
python3 holladay_cf_buildindex.py   # rebuild index.csv from raw/ + raw/_fetch_log.jsonl
```

`buildindex.py` recomputes `format` (pdftotext char count ≥200 ⇒ `text`) and pulls `source_url` +
`sha256` from the fetch log — idempotent. Per-file candidate/office/date metadata is a hand-verified
mapping inside the script (auditable against the filenames + `holladay_races.csv`).

## Caveats

- **Acquisition-only** — no dollars, no totals, no OCR. A future extraction pass (OCR/vision on the
  39 scanned forms → `filing_totals.csv` → `cycle_totals.py` dedup) is required before any spend
  figure.
- **Coverage is COMPLETE for every in-scope ballot candidate (2021/2023/2025)** — see the table in
  AVAILABILITY.md. Discrepancy flags (Wilson, Gray 2023 D5, Durham 2023, the empty 2019 folder) are
  recorded there; `election_results/` was **not** edited.
- **Jan-2026 roster seam**: Dahle→Fotheringham (Mayor), Brewer→Sundwall (D1), Fotheringham→Bradley
  (D3). Fotheringham appears across 2017/2021 (D3) and 2025 (Mayor) — join date-aware.

## 2026-07-17 — CF VISION TRANSCRIPTION (tranche 1, 2025 cycle) — vision/ caches written

Transcribed the **2025-cycle scanned C&E filings** via `/cf-vision-transcribe` (Read-tool
vision, **$0 Anthropic API**). **11 of 12** renderable scanned 2025 filings cached (167
contributions + 189 expenditures); the 6 `statement`/`conflict` disclosures are out of scope
(not C&E reports).

- **Cache contract:** filenames use **pure `sha1(index_path)[:8].json`** + WJ vision schema +
  a `_meta` block (index_path, candidate, office, filing_type, election_year, source_pdf, pages).
- **CACHE-KEY COLLISION (holladay-specific, resolved):** `raw/2025_city_bradley-10282025.pdf`
  and `raw/2025_city_fotheringham10282025.pdf` both end in "10282025" (all-hex), so the West
  Jordan `_did8` *trailing-hex shortcut* would collide them to `10282025.json`. Resolved by using
  **pure sha1(index_path)** (no shortcut) — collision-free and consistent with the other 5 wave
  cities (whose filenames never triggered the shortcut). A future holladay `build_finance.py`
  MUST key on pure sha1(path) or docid, NOT trailing-hex (feed TODO Tier C cache-key standardization).
- **~~INDEX DEFECT~~ — MISDIAGNOSIS, CORRECTED 2026-07-17 (wave 2):** the tranche-1 note claimed
  `raw/2025_city_bradley-10282025.pdf` held **Paul Fotheringham / Mayor** content (a duplicate of
  `raw/2025_city_fotheringham10282025.pdf`, totals 2,300 / 9,192.46 / 1,338.02) and should be
  corrected/removed. **That was WRONG.** Re-rendered and read all 3 pages 2026-07-17: the file is
  **genuinely Natalie Bellamy Bradley / City Council District 3** (cover totals: contrib >$50 = $0,
  ≤$50 aggregate = $50, expenses $35.45, ending balance $469.16; Form A = Mark Rothacher $50; Form B
  = Holladay City filing fee $50 + Fund Hero $8.59 + Square Space $26.86). The on-disk sha256
  (`e54c0fa7…`) is byte-identical to the fetch-log entry for the `Bradley.10282025.pdf` URL and to
  the index-recorded hash — the file never changed and was never Fotheringham. **Root cause of the
  false alarm: a scratchpad working-file collision** — both files end in `10282025`, and the
  tranche-1 render used a shared output prefix, so the Bradley "read" actually showed the already-
  rendered Fotheringham images. **Resolution:** the index row's candidate/office/match fields were
  already correct (NO defect); its `date` was refined `2025-10-27` → `2025-10-24` (the form's printed
  DATE / reporting-period-end / RECEIVED stamp all read 10/24/25, filed for the Oct-28 deadline). The
  Bradley Oct-24 filing was transcribed to `vision/89aca2a7.json` (the row tranche-1 wrongly skipped).
  Bradley's full 2025 set (Oct 7 `ff02730e` + Oct 24 `89aca2a7` + Final `8f64a120`) is complete — no
  acquisition gap. **Lesson (feeds the cache-key-standardization TODO): render each PDF into a UNIQUE
  working dir, never a shared prefix.**
- **STRUCTURING PENDING:** no `build_finance.py` yet — additive caches only; owner-gated later work.
- **Holladay "Financial Declaration" form:** line-2 "$50 or less" aggregate → `contributions_50_or_less`;
  **no beginning-balance line** (`beginning_balance` null throughout); itemized dates often
  month/day only (verbatim, no year inferred). Self-loans (Fotheringham/Watts "Cash Loan")
  preserved as contribution rows; a few cover-vs-schedule ~$300 gaps (= the $50-or-less aggregate)
  and a Watts duplicate row left verbatim/unreconciled.
- Backup: `_backups/2026-07-17-cf-vision-t1/holladay/` (greenfield — nothing pre-existed).

## 2026-07-17 — CF VISION TRANSCRIPTION (tranche 2, wave 2: 2023 + 2021 cycles + the Bradley fix)
Transcribed the remaining scanned C&E filings via `/cf-vision-transcribe` (Read-tool vision,
**$0 Anthropic API**), 2023 cycle first then 2021, same cache contract as tranche 1
(`sha1(index_path)[:8].json`, WJ vision schema + `_meta`). **13 new caches → 24 total.**

- **2025 (1):** `89aca2a7` — the Bradley Oct-24 filing tranche-1 wrongly skipped (see the corrected
  MISDIAGNOSIS note above). Bradley 2025 set now complete.
- **2023 cycle (7):** Drew B. Quinn ×3 (`63818360` 10/24 interim, `6f7880ca` 7-day, `37b07041`
  Final), Matthew Collin Tracy ×3 (`4e6c5b17` 7-day, `528e53ee` interim, `2ba338e1` Final), Emily
  Gray `467c8691`. **Gray (indexed `filing_type=statement`) IS a real Financial Declaration C&E
  form** (full cover totals + Form A/B) — transcribed, `_meta.filing_type` kept `statement` to match
  the index.
- **2021 cycle (5):** Melissa Blackham Hilton ×2 (`f6ce8701` Oct interim, `96bee2ad` Final), Paul S.
  Fotheringham `7b4e73b8` (Oct interim, unopposed — Form A "none", $35 filing fee only), Robert M.
  Dahle ×2 (`4ffeb1b5` Oct interim, `69b7d792` Final). All single-report PDFs (no bundling).
- **Verbatim source quirks captured (NOT reconciled — anti-fabrication):** Drew 2023 interims carry
  handwritten previous-/negative-balance lines (recorded as `beginning_balance`; each report's
  arithmetic checks out); Tracy interim `528e53ee` Form A itemized ~3,385 vs cover 3,345 (source
  cover-vs-schedule gap); Dahle Final `69b7d792` Form B rows sum 7,232.58 vs cover line-3 7,238.52
  (apparent cover digit-transposition); Hilton ending balances printed parenthesized/negative
  verbatim; Gray has one in-kind $3,000 (Russ Gray, Design Services) flagged `in_kind:true`. Some
  self-loans preserved as contribution rows (Dahle "LOAN TO CAMPAIGN" bracket).
- **Still NOT vision-transcribed (honest, out of this task's scope):** the **2017 bonus** scanned
  C&E filings (Petersen, Roach, Fotheringham-primary, Dahle-Aug — 4, pre-scope) and the **COI ethics
  disclosures** (excluded by design — not C&E reports). Every in-scope **2021/2023/2025** scanned C&E
  filing now has a `vision/` cache; the 13 born-digital `text` filings were never scanned-vision
  candidates.
- **STRUCTURING STILL PENDING** — no `build_finance.py` (owner-gated); these remain additive caches.
- Backup: `_backups/2026-07-17-wave2/holladay/` (index.csv + docs + tranche-1 vision snapshot +
  buildindex.py).

## 2026-07-17 — STRUCTURED LAYER BUILT (cf-structuring wave; family `vision_cache`)
`build_finance.py` (shared helpers `scripts/campaign_finance/vision_lib.py` + `driver.py`) now
writes the four DERIVED, regenerable CSVs — `contributions.csv` (308) / `expenditures.csv`
(372) / `filing_totals.csv` (40 = the FULL C&E inventory: 36 vision-transcribed + 4 below-floor
2017 inventory-only rows) / `cycle_totals.csv` (18 candidate-cycles). `validate_finance.py` →
**PASS (0 fails**; the 12 WARNs are the excluded COI rows, by design). `scripts/validate_city.py
holladay_city_council/` → **0 FAIL** (22 PASS / 4 WARN, pre-existing).

- **12 BORN-DIGITAL `format=text` C&E filings were vision-transcribed too (→ 36 caches).** Unlike
  midvale's junk-text templates, Holladay's `text` layer is REAL money (verified via `pdftotext
  -layout`): 2021 Brewer ×2, 2025 Sundwall ×3, Bilstad ×2, Jones ×3, Watts Oct-7, Wilson Final.
  Leaving them inventory-only would DROP real money, so they were transcribed from the
  authoritative born-digital text at build time (cache `_meta.transcription` records this). These
  earn `high` confidence when they reconcile; the 24 scanned caches earn `medium`.
- **Scope:** 12 COI ethics disclosures EXCLUDED by `in_scope_fn` (not C&E reports); the 4
  below-2020-floor **2017** bonus scans stay IN as honest inventory-only rows (unknown totals,
  dated reason, `low`). Every one of the 52 index rows is accounted (40 filing_totals + 12 COI).
- **In-kind convention — `reconcile_cash_only=True`.** Holladay's cover total (Form-A line 1) is
  CASH-ONLY: Gray 2023's $3,000 in-kind (Russ Gray, Design Services) is EXCLUDED from her printed
  9,297.00 cover (proof: cash-only itemized 9,582 − 285 `$50-or-less` aggregate = 9,297 exactly).
  Gray's is the ONLY in-kind row across all 36 caches.
- **Per-candidate regimes** (printed by every build; eyeballed): 2021 **Brewer / Hilton / Dahle
  are CUMULATIVE** (each report restates cycle-to-date → latest/Final wins, earlier snapshots
  marked superseded); **2023 + 2025 filers are PER-PERIOD** (each report is its own period; the
  balance chain proves disjointness). Query `cycle_totals.csv` — it encodes the dedup; never sum
  `filing_totals`.
- **`cycle_overrides.csv` (6 rows).** For a PER-PERIOD filer, cycle_totals' summary-vs-interims
  rule drops the Dec "Final" (which is itself just another period), undercounting. Overridden
  where the per-report BALANCE CHAIN links exactly (honest to sum): **Quinn 2023, Bradley 2025,
  Fotheringham-Mayor 2025** (a ~$50k race whose $17k Final period the generic rule dropped),
  **Sundwall / Bilstad / Jones 2025**. Each reason cites the per-filing figures.
- **NOT overridden — left computed + flagged (cannot honestly sum):** **Tracy 2023** (balances
  don't chain; the Nov-1 "period not stated" filing appears to overlap the 7-day report),
  **Watts 2025** and **Wilson 2025** (donors/expenditures RECUR across the primary and general
  reports — 7 shared donor names in Watts Aug↔Oct-7, non-chaining balances — so a clean cycle
  sum is genuinely ambiguous). cycle_totals carries a `MIXED` review flag on Watts/Wilson;
  Wilson's raised therefore excludes his Final $10,001 self-loan (flagged, not fabricated).
- **Reconciliation:** 16/40 filings reconcile BOTH sides against printed covers. The rest flag
  on two honest, structural patterns (kept verbatim, NEVER adjusted): (a) the **`$50-or-less`
  cover gap** — Form-A line 1 counts only >$50 donors, but itemized rows include the ≤$50 donors,
  so `contrib!=stated` by exactly the aggregate; (b) the **filing-fee re-listing** — 2025 filers
  print the $50 Holladay filing fee on every Form B but omit it from the period's stated total, so
  `expend!=stated` by $50. Plus the documented one-off source discrepancies: Tracy interim
  ~$40/~$100 cover-vs-schedule, Dahle 2021 Final −$5.94 cover transposition, Wilson cover 10000.1
  vs itemized 10,001.00, Sundwall Final's $69 line under-adding its rows (~$79 by the chain).
- **No `donor_aliases.csv` / `finance_overrides.csv`** (both optional; none needed — no verified
  cross-spelling merges, and mismatches stay flagged verbatim, not corrected). Minor known
  limitation: `Douglas Ty Brewer (self)` classifies `donor_type=unknown` (the index stores the
  abbreviated first name "D. Ty Brewer", so the deterministic self-match can't fire) — not
  fabricated; leave as-is.
- Regenerate: `python3 build_finance.py` then
  `python3 scripts/campaign_finance/cycle_totals.py holladay`. Backup:
  `_backups/2026-07-17-cf-structuring/holladay/` (docs + index + pre-build vision snapshot).

## 2026-07-18 — CF EVIDENCE-PASS ADJUDICATION (Tracy 2023, Watts 2025, Wilson 2025)
Owner-authorized row-level adjudication of the three candidate-cycles the cf-structuring
wave left computed-and-flagged. All three resolved to documented `cycle_overrides.csv`
rows (basis=`override`); no source values touched, no caches/CSVs hand-edited. Method:
compare itemized rows across a candidate's filings, dedup EXACT cross-report re-listings
(same date+name/recipient+amount), keep different-date repeats. Validators after:
`validate_finance` PASS (0 fails / 12 COI warns) · `validate_city` 0 FAIL (22 PASS/4 WARN).
Backup: `_backups/2026-07-18-cf-adjudication/holladay/`.

- **Matthew Tracy 2023 D4 — OVERRIDE 4020/3924.19 → 4389.17/3924.19.** Rendered the 3
  scanned covers: the filing LABELED "7-day" (cache `4e6c5b17`) is actually stamped **NOV
  14 2023** (bal $230.83) and the "period not stated" one (`528e53ee`) is signed **Oct 24
  2023** (bal $64.80) — i.e. the index dates are ~reversed. With that chronology the 3
  reports DO chain: $64.80 → $230.83 → Dec-21 Final $0.00 (within 2¢), so Tracy is a
  per-period filer and the Dec-21 Final is a real period (not a summary). Two interims
  overlap Oct-16..23 with exactly **two** exact re-listings: **Michael McDonald (web page)
  Oct-23 $600** (in both covers → deduped from spent) and **Womens Democratic Club Oct-16
  $50** (≤$50, in neither Form-A >$50 cover → immaterial to raised). raised=3345+675+369.17;
  spent=(3315.20+608.99+600)−600. Residual: the filer's stated $0 ending only balances by
  double-listing the $600, so the unique-transaction ending implies ~$600 surplus — filer
  bookkeeping, verbatim.
- **Daren Watts 2025 Mayor — OVERRIDE 64,735.33/70,370.76 → 65,135.33/62,880.49** (MIXED
  cleared). Per-period filer (each report's ending = its own raised−spent from 0). Summed
  all 4 covers, removed EXACT cross-report re-listings. Donors: only **Tom Rosenberg 8/3
  $200** (Aug↔Oct-7) and **Chris Bowler 10/23 $1,000** (Oct-28↔Final) are same-date+amount
  re-listings (−$1,200); the ~7 other recurring donors (Russ/Brent/Greg Watts, Ellis Ivory,
  Brian Hall, John Dunn, Shane Topham, Brad Reynolds) recur on DIFFERENT dates = real repeat
  gifts, kept. The material fix is on the SPEND side: the **Oct-7/Oct-28 10/1–10/6 re-listed
  expenditure block ($13,045.37)** + Aug/Oct-7 boundary ($63.10) + Oct-28/Final boundary
  ($120.25) = **−$13,228.72** the prior sum-interim double-counted. Residual: the within-Aug
  Greg Watts 7/10 $950-listed-twice is kept verbatim (reconciles to the $31,163.33 cover).
- **Zac Wilson 2025 Mayor — OVERRIDE (Final now INCLUDED) 28,913.37/24,201.89 →
  38,914.37/27,017.01** (MIXED cleared). His Sept-11 Final is a genuine NEW period, NOT a
  restatement: sole contribution is his **$10,001 self-loan dated 8/1** (absent from the Aug
  filing) and every expense dates 7/31..9/1, entirely AFTER the Aug filing's last expense
  (7/30) — zero row overlap (verified). So Aug + Final sum with no double-count. raised uses
  the itemized $10,001.00 (cover prints $10,000.10, the documented transposition typo).
  Residual: the Final's stated ending $11,469.74 is ~$542.62 short of a clean cumulative
  chain from Aug's $4,826.48 — filer ending-balance bookkeeping; the disjoint contribution/
  expense totals summed here are unaffected.
