# VISION_CITIES_ROLLOUT — structured CF layer for the vision-cached cities

Owner-approved 2026-07-17. Reference implementation: **midvale** (`build_finance.py` +
`cycle_overrides.csv`, built + validated the same day). Shared machinery — do NOT fork:
- family **`vision_cache`** (`families/vision_cache.py`; parse() is an honest empty stub),
- **`vision_lib.py`** — cache→rows (`build_result`, incl. the multi-report `reports[]`
  bundle path + the label-based **Column-A restatement exclusion**), verbatim `vmoney`/
  `vdate` normalization, `empty_result` inventory rows, and **`detect_regimes`**
  (per-candidate-cycle cumulative/incremental, evidence-tiered, decisions printed),
- `driver.py` accepts a CALLABLE `dedup_mode(candidate, year, members)` (string modes
  unchanged — proven byte-identical on taylorsville/west_jordan/millcreek rebuilds).

## The 13 cities
cottonwood_heights, herriman, holladay, murray, riverton, south_salt_lake, bluffdale,
kearns, emigration_canyon, alta, copperton, white_city, magna.

## Per-city build_finance.py (copy midvale's; ~120 lines)
1. `_meta` from the city's index.csv columns (they differ slightly — check headers;
   `document_id = vision_lib.cache_key(ix["path"])` ALWAYS; `filing_regime` only if the
   city has a documented annual-vs-election regime split, else "").
2. `in_scope_fn`: exclude COI/ethics disclosures, candidacy declarations, and 2026
   council-vacancy applications (each city's CLAUDE/AVAILABILITY names its exclusions);
   below-floor bonus years STAY IN as inventory-only rows (the midvale convention).
3. `rows_override_fn`: cache → `vision_lib.build_result`; no cache → `vision_lib.
   empty_result(<dated, city-specific reason>)`. Distinguish reasons honestly:
   below-floor / junk-text-layer / duplicate-source copy / acquisition-blocked.
4. Regime pre-pass → `detect_regimes` → callable dedup_mode + per-row `is_incremental`
   (midvale's `main()` shows the wiring). EYEBALL the printed decisions against the
   filings before accepting.
5. `reconcile_cash_only`: check 2–3 filings with in-kind rows — does the printed cover
   TOTAL include in-kind at face value? (midvale: yes → False). The driver's
   alt-convention fallback note will tell you if you guessed wrong.
6. After the build: `cycle_totals.py <city>`; then eyeball every per-period filer whose
   final/"summary"-typed filing is itself a period report → documented
   `cycle_overrides.csv` rows (midvale's 5 rows are the template; reason must cite the
   evidence). NEVER override a filing you cannot honestly sum (midvale's Fair
   column-swap precedent — leave computed + flagged).

## Known per-city landmines (from the wave-2 ledger — verify, don't assume)
- **riverton**: 2023 "financial-2024" caches are 3-report bundles (Column-E covers;
  Haymond's cover honestly null); the interim+summary overlap is BY DESIGN — the bundle
  restatement rule + regime detection must prevent double-counting. Pierucci's 10-24-23
  filing is an ACQUISITION GAP (state mis-publication — no cache exists; inventory row).
- **emigration_canyon**: Bowen 2016 (`773be790`) is a two-report PDF cached as the
  November report only — do NOT treat the cache as the whole filing; note it, queue the
  reports[] re-vision as a follow-up.
- **bluffdale**: 1 multi-report `reports[]` bundle (Pavlakis 2025); 2 pre-floor 2017
  scans stay inventory-only.
- **south_salt_lake**: several filers list cumulative YTD on every report ("Total this
  Period" ≠ line-sum) — regime detection should catch it; Campos 2025 cover totals are
  stale carryover (expect a reconcile flag, not an error).
- **holladay**: caches keyed pure `sha1(path)[:8]` (the 10282025 trailing-hex collision
  lesson); Cottham 2023 is cover-only (itemization honestly empty → totals-only note).
- **white_city**: 3 filers print non-zero covers over BLANK schedules (Mahoney,
  Cardenaz, Price) → totals-only(no itemization) UNKNOWN reconciles, by design.
- **kearns**: 2023 (EasyVote auth-wall) + 2025 (Cloudflare) cycles are acquisition
  gaps — inventory rows only; Richards 2019 interim subtotal mismatch stays verbatim.
- **magna**: 2023 = EasyVote gap (no filings exist to build); 2016–2019 township scans
  (43) are below-floor inventory-only.
- **murray**: two regimes may apply (check for annual statements); Evans docx cache
  `577872d2` is normal; 2017/2019 below-floor inventory-only.
- **cottonwood_heights**: honor `duplicate_of` (Prazen "final" = re-upload of his Oct-28
  interim → the duplicate row must be superseded/excluded from cycle math, and his
  GENUINE final is an acquisition gap); Bracken/Daurelle filing-period corrections are
  already in the index.
- **alta**: 7 born-digital `format=text` reports have REAL text (unlike midvale's junk
  — Bourke's $2,000 Abundance PAC line lives there): parse them (pdftotext at build,
  simple grammar) or vision them — do NOT leave that money out; Schilling 2023 has 4
  duplicate filings (count once); 2021 Byrne $5,000 self-funded should land
  `donor_type=candidate-self`.
- **copperton / white_city / EC**: tiny towns — most filings are fee-only/$0; expect
  high totals-only/zero counts; that is the honest shape, not a build failure.

## Verification checklist (every city, before reporting done)
- [ ] `build_finance.py` runs clean; regime decisions printed + eyeballed.
- [ ] `validate_finance.py <city>/campaign_finance` → 0 FAIL.
- [ ] `cycle_totals.py <city>` run; overrides documented where the summary-is-a-period
      hazard applies; review flags explained in the report.
- [ ] Spot-check ≥3 filings' CSV rows against their cache JSONs (counts+amounts+names)
      and ≥1 against the raw PDF page images.
- [ ] Every index row is in `filing_totals.csv` or excluded by `in_scope_fn` with a
      named reason; no silent drops.
- [ ] `scripts/validate_city.py <city_dir>` unchanged (0 FAIL).
- [ ] Backups of any pre-existing modified file in `_backups/2026-07-17-cf-structuring/
      <city>/`; dated sections appended to the city's CF CLAUDE.md + AVAILABILITY.md.
- [ ] NO federation (`build_cities_db.py`), no TODO/HANDOFF edits — report instead.
