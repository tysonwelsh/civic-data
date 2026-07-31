# Riverton City — Campaign-Finance Disclosures: Availability

**As-of:** 2026-07-13 · **Layer:** ACQUISITION-ONLY (raw filings retained; no OCR/vision
extraction, no dollar totals — those are deferred). **Cycles in scope:** 2021 (D3/D4/Mayor),
2023 (D1/D2/D5), 2025 (D3/D4/Mayor).

## What was checked (search order)

1. **City recorder / elections pages — PRIMARY, richest source.** Riverton (Revize CMS) keeps
   candidate disclosures on two live pages:
   - `government/elections/archived-disclosures.php` — "Conflict of Interest & Financial
     Disclosures" (created "to meet the legal requirements passed in HB80 in 2024"). Carries the
     **2023-cycle year-end financial reports** (`<name>-financial-2024.pdf`, 5 candidates) plus
     annual sitting-official Conflict-of-Interest forms (2025/2026).
   - `government/elections/candidates.php` — the **2025 declared-candidate roster** with each
     2025 candidate's full filing packet (declaration, conflict, and the 4-report finance series).
   - Files are stored flat under `departments/recorder/elections/<slug>.pdf` and served at the
     canonical URL (the `?t=` query is only a Revize cache-buster). **Older cycle files not
     linked on the current pages remain live on the server** and were recovered by filename.
2. **Wayback Machine (CDX)** — used as a **discovery index** for filenames no longer linked
   (all captures of `departments/recorder/elections/*` were 302 Revize redirect stubs, so the
   PDFs themselves were fetched from the **live** server, not from Wayback). This surfaced the
   **2021-cycle finance reports** (McCay, Buroker, Staggs), the **2023 declarations**
   (Pierucci, Gatti, McDougal), and the declared-but-unballoted filers below.
3. **Tyler EagleWeb / `*.contentmanager.tylerapp.com`** — **none exists** for Riverton (no such
   subdomain resolves). Riverton is Revize + Granicus, not Tyler.
4. **State — `disclosures.utah.gov/municipal`** (GET-navigable county→year folder tree) — holds a
   **`salt lake_2023_Riverton`** folder with the **2023-cycle interim reports** (filed 10.24.23,
   11.14.23, 12.21.23) for all five candidates — filings the *city* page does NOT publish (city
   only posts the year-end summary). **No `2021` Riverton folder; the `2025` entry only links back
   to the city page** (city hosts 2025). These 15 state PDFs are `source=state_lg_municipal_disclosures`.
5. **SLCo Clerk** — posts county/state filings, not municipal (per skill guidance); not a source
   for Riverton municipal candidates.

## Coverage vs the election roster (`election_results/riverton_races.csv`)

**Every candidate who appeared on a ballot in an in-scope cycle has campaign-finance filings.**

| Cycle | Ballot candidates (office) | Finance filings held | Status |
|---|---|---|---|
| **2021** | McCay (Council D3), Buroker (Council D4), Staggs (Mayor) — all uncontested | 1 report each | **COMPLETE** |
| **2023** | Pierucci (D1), McDougal + Gatti (D2), Haymond + Winters (D5) | 4 each = 3 state interims + 1 city year-end | **COMPLETE** |
| **2025** | Buroker + McCay (Mayor), Johnson + Lance (D3), Smith + Park (D4) | Primary/28-Day/General/Post-Election series (2–5 each) | **COMPLETE** |

Money-report count by candidate: 2021 McCay/Buroker/Staggs ×1; 2023 all five ×4; 2025 McCay ×5,
Buroker ×4, Johnson/Smith ×3, Lance/Park ×2. (2025 losers Lance/Park have no Post-Election
report — expected; the winners/mayor filed the follow-up.)

## Discrepancy FLAGS (do NOT edit `election_results/` — these are recorded here only)

1. **David Almond — declared 2023 Council District 5 but never balloted.** `david-almond-declaration-2023.pdf`
   (sworn 2023-06-07, D5) exists, yet `riverton_races.csv` 2023 D5 lists only Haymond & Winters.
   Almond withdrew/was removed before the ballot (a third D5 filer would have forced a primary; no
   2023 primary is in the county SOVC → consistent with withdrawal). **No finance report** filed.
   Declaration captured for provenance (`filing_type=declaration_of_candidacy`).
2. **John Scott — declared 2025 Mayor; the un-named 3rd primary candidate.** `john-scott-declaration-2025.pdf`
   (sworn 2025-06-06, Mayor). `riverton_races.csv` shows the 2025 Mayor **primary** had
   `n_candidates=3` but names only winner Buroker + runner-up McCay — Scott is the eliminated third.
   **No finance report** published by Scott.
3. **Matt Renlund — declared 2025 Council District 4 but never balloted.** `matt-renlund-declaration-2025.pdf`
   (sworn 2025-06-06, "Council Member #4"), yet 2025 D4 lists only Smith & Park. Withdrew before the
   ballot. **No finance report** published.
4. **2023 filing series is split across two publishers** — the three interims (Oct/Nov/Dec 2023) live
   only on the **state** site; the year-end summary lives only on the **city** page. Neither source is
   complete alone; this dataset merges both.
5. **2021 finance reports are unlinked legacy files** — recovered by Wayback-discovered filename from
   the live server (the current archived-disclosures page begins at the HB80/2024 era).
6. **⚠ MIS-PUBLISHED SOURCE FILE — `2023_pierucci_state_10-24-23_redacted.pdf` actually contains
   Spencer HAYMOND's report, not Pierucci's** (found 2026-07-17 wave2 during CF vision transcription).
   The state file `municipal.utah.gov/salt lake/2023/Riverton/Andy Pierucci_Campaign Finance_10.24.23
   (redacted).pdf` is, in its printed content, the **Riverton City 28-Day Report for Spencer Haymond,
   Council District 5** (contributions $4,337.00 / expenditures $2,993.84 / ending $1,343.16 — identical
   to Haymond's own 28-day interim `2023_haymond_state_10-24-23.pdf`, confirmed line-for-line). The Lt.
   Governor's office evidently uploaded the wrong PDF under Pierucci's filename. Consequence: **Andy
   Pierucci's actual 10-24-23 (28-Day) interim was never acquired** — an honest acquisition gap. His
   OTHER 2023 filings ARE held (11-14-23 + 12-21-23 interims as born-digital text, plus the
   `pierucci-financial-2024` year-end SUMMARY which carries his cumulative cycle figures), so his cycle
   is substantially covered. **No vision cache was written for this file** (transcribing it would have
   attributed Haymond's donors to Pierucci — a fabrication); the would-be cache `vision/a9133262.json`
   was deliberately NOT kept. `index.csv` still catalogues the row under `candidate=Andy Pierucci`
   (city-faithful to the state's filename/slot) — left unedited pending owner re-acquisition of
   Pierucci's real 28-day report. Do NOT read `2023_pierucci_state_10-24-23_redacted.pdf` as Pierucci
   data.

## Double-count trap (per SKILL §6)

Riverton candidates file **multiple reports per cycle** (2023 = 3 interims + 1 year-end summary;
2025 = Pre-Primary + 28-Day + General + Post-Election). **Never sum a candidate's filings** for a
cycle dollar total — the interims are cumulative-to-date restatements and the summary is the
cumulative final. Any per-candidate/per-race total must be computed with the repo dedup
(`scripts/campaign_finance/cycle_totals.py`) at extraction time, not by adding rows here. Note also
`tawnee-mccay-campaign-finance-statement-10.25.pdf` was uploaded the same day as her 28-Day report and
is likely the same statement (`filing_type=statement`, flagged possible duplicate).

## Formats

30 born-digital (`text`) / 30 image-only (`scanned`) of 60 PDFs. The **2023 city year-end summaries,
most 2023 state interims, the 2021 McCay report, all declarations, and the 2025 primary/general
reports are scanned**; the 28-Day and Post-Election 2025 reports, the 2021 Buroker/Staggs reports,
and the conflict forms are born-digital. OCR/vision extraction is deferred (acquisition-only);
`extraction_method='none (raw acquisition; OCR/vision deferred)'` on every row.

## Not captured (deliberate)

- Annual sitting-official **Conflict-of-Interest forms** on `archived-disclosures.php` (Staggs/
  Pierucci/McDougal/McCay/Buroker/Haymond 2025; six members 2026) — these are officeholder COI
  filings, not campaign-cycle candidate disclosures. Candidate COI forms filed as part of a 2025
  campaign packet ARE captured (`filing_type=conflict_of_interest`).
- Candidate photo JPGs on the elections path (not disclosures).

## 2026-07-18 — STRUCTURED MONEY LAYER BUILT

The derived layer (`filing_totals.csv` 41 / `contributions.csv` 303 / `expenditures.csv` 308 /
`cycle_totals.csv` 14) is built (`build_finance.py`). `validate_finance.py` PASS (0 fails).
Read `cycle_totals.csv` for candidate/race totals. Highlights vs the coverage table above:

- **All in-scope money reports are transcribed** (40 vision/text caches), including the
  born-digital `format=text` reports the acquisition doc left "deferred". Those text reports are
  NOT clean pdftotext — they are degraded fillable-form renders or (2021 Buroker/Staggs and
  several 2025 reports) handwritten scans mislabeled `format=text`; they carry REAL money and were
  transcribed rather than dropped.
- **Pierucci 10-24-23 acquisition gap (flag #6 above):** represented as one honest inventory-only
  `filing_totals` row (blank totals + dated reason); NO cache written. Pierucci's cycle total
  (5,540 / 2,817.78) is carried by his year-end summary's printed Column E, so his cycle is
  substantially covered despite the missing 28-Day itemization.
- **McCay `statement` (`tawnee-mccay-campaign-finance-statement-10.25.pdf`)** is EXCLUDED from the
  money layer as a byte-identical duplicate of her 28-Day report (same sha256) — counted once via
  the 28-Day filing. Declarations (12) and conflict-of-interest forms (6) are excluded as
  non-money reports.
- **2025 mayor race totals (contested):** Buroker 32,350.00 raised / 26,932.59 spent; McCay
  30,690.55 / 26,419.77 (from each filer's printed Column E, via `cycle_overrides.csv` — the
  Post-Election report is itself a period, not a cumulative final). 2021 Staggs (uncontested mayor)
  raised 28,750 but itemized nothing (totals-only).

### Follow-ups (report-only; not blocking)
1. **McCay 2025 primary cache (`f233622b`) minus-sign quirk:** the filer wrote the first Schedule-B
   page's amounts as negatives (−) but totaled them positive; the cache preserved them verbatim, so
   the filing's expend side reconciles FALSE (itemized 5,026.66 vs cover 10,386.76). Cycle spend is
   correct via the Column-E override. Optional: re-vision to record the intended positive values.
2. **Buroker 2025 general cache (`cdaabfda`) "$3,000,00" filer typo** → `vmoney` reads 300,000 (a
   100× phantom in that filing's `itemized_contrib_sum`/`self_funded_amount`). Kept verbatim +
   flagged; documented in `finance_overrides.csv`. Cycle total is unaffected (uses the printed
   cover 4,000). Correct when `finance_overrides` is wired into the build, or fix the cache to
   3000.00 (the value the filer's own $4,000 subtotal proves).
3. **`donor_aliases.csv` is header-only** — org/PAC donors (Salt Lake Board of Realtors, Utah
   Realtors Association, SLCo Firefighters Local 1696, Republican Women Lead, etc.) currently take
   tier-1 `donor_type` (mostly `business`/`individual`); a curated alias pass could tag PACs.
