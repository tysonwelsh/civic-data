# cache_county / elections — verification report

**Build date:** 2026-07-20. **Method:** every parsed layer reconciled against the
county's own summary/certified documents (`verify_elections.py`, rerunnable), the
held city's independently audited layer (logan_city_council), and external news
reporting. All gates **PASS**. Raw originals byte-verified in `sources.csv`
(sha256; 94 files, zero unrecorded).

## Reconciliation gates (verify_elections.py — ALL PASS)

| Gate | What it proves | Result |
|---|---|---|
| 1a | 2023 municipal general **details** (precinct grain, 161 blocks) sums exactly to the **certified 12/01/2023 summary**, all 64 candidate totals in 16 contests | PASS — exact |
| 1b | 2020 primary precinct report == official summary (18 candidate totals) | PASS — exact |
| 1c | 2020 general canvass precinct (570 pages) == official canvass summary (100 candidate totals, incl. re-joined wrapped names) | PASS — exact |
| 1d | 2022 primary precinct == official summary (12 candidate totals) | PASS — exact |
| 1e | 2026 primary **public** precinct report is a strict subset of the summary (whole small precincts withheld: 90 of 126 precincts published; 210 votes total shortfall) — every published number ≤ summary, none contradicts | PASS — documented subset |
| 2 | 2025 portal Electionwide totals vs precinct sums: 11 candidates differ, all by **+1..+3 votes** (the portal's unassigned bucket — same artifact logan module documented); summary totals are authoritative in the derived layer | PASS |
| 3 | **All 34 overlapping Logan audited candidate totals (2023 primary+general, 2025 primary+general) match the logan_city_council audited layer exactly** — incl. the 2023 recount-episode figures (Anderson 3,449 / Johnson 2,892 / Simmonds 2,419 / Needham 2,400 / Lee-Koven 2,388 / Bennett 1,082; the 19-vote seat margin) and the 2025 margins (mayor −1,299; council seat −84) | PASS |
| 4 | by_contest internal: 82 contests, ranks 1..n, votes non-increasing, no aggregate pseudo-candidate leaked | PASS |
| — | Loader conformance: all 285 by_contest rows insert into the `election_result` schema with the exact types `scripts/build_cities_db.py::load_election_result()` uses (simulated in-memory) | PASS |

External cross-checks: 2021 North Logan mayor — canvass winner LYNDSAY PETERSON
(1,708 / 68.65% vs Nelson 780) confirmed by Cache Valley Daily / successor
reporting (she took office as North Logan's first female mayor); the news
election-night figures (1,076/519, 67.5%) are lower than the final canvass
values, the normal election-night-vs-canvass gap (same pattern the logan module
recorded for 2019). 2023 Logan recount outcome corroborated by
sltrib/UPR/Cache Valley Daily (via the logan module's ELECTION_VERIFICATION.md,
independently re-confirmed here by gate 3).

## FINDING A — RCV and the county canvass

**The Cache County canvass contains no RCV tabulation in any acquired year, and
RCV contests are simply ABSENT from it, not summarized.** Specifics:

- The only Cache municipality found to have used RCV is **Nibley, in 2021**
  (mayor + council; Jacobsen elected mayor, Beus + Larsen council — external).
  Nibley's 2021 general is **entirely absent from the county's 2021
  publications**; Nibley **self-administered and self-canvassed** it (its city
  council accepted its own canvass on 2021-11-15 — evidence PDF
  `raw/pmn-785553-nibley-2021.pdf`, the town's PMN minutes).
- **North Logan did NOT use RCV** in 2021/2023/2025 — it held plurality
  primaries in all three cycles (present in the county primary canvasses) and
  its general-election results are plain vote-for-N totals. (The aside in
  `logan_city_council/election_results/CLAUDE.md` naming North Logan as an RCV
  city appears to be wrong; Logan's own no-RCV conclusion is unaffected.)
- 2023 + 2025 state-portal contests are all `contestType: Candidate` with
  `rankedChoiceSummaryResults: null`.
- **Consequence for consumers:** nothing in this module's `rank_in_contest`
  is ever an RCV final — it is always plurality order — and no SOVC
  first-choice ordering is presented as an RCV result because no RCV contest
  exists here at all. A future Nibley-2021 recovery would have to come from
  Nibley's own records (queued as an acquisition gap).

## FINDING B — who administered Logan's municipal elections

- **2019: the county published NOTHING for any municipal election** — the
  county results page jumps 2018 → 2020, verified on the live page AND the
  2020-08-13 Wayback snapshot (post-2019-canvass). Logan self-administered
  2019 (city-certified PDFs live in `logan_city_council/election_results/raw/`).
- **2021: Logan self-administered and is absent from the county canvass.** The
  county's 2021 publications (this module's
  `cache-2021-general-summary.pdf` / `cache-2021-primary-precinct-summary.pdf`,
  byte-identical to the evidence copies logan holds) contain only the smaller
  towns — no Logan contest.
- **2023: the county administered Logan for the first time** — Logan appears
  in the certified county canvass (this module reproduces logan's audited
  figures exactly, gate 3). 2025: county-administered via the state portal.
- **Consequence for the future logan re-point:** logan's 2019 + 2021 races can
  NEVER be re-pointed to this canonical (they do not exist here — Logan's own
  city PDFs are the sole primary source, like millcreek-2016 in the SLCo
  model); 2023 + 2025 are re-pointable (byte-level agreement already proven at
  the candidate-total grain).

## Recording ceilings (the source's limits, not ours)

- **2021 municipal general: electionwide grain only** — the county's final
  posted document is an Election Summary Report dated 11/09/2021 **labeled
  UNOFFICIAL RESULTS**; no precinct-grain or certified-label 2021 general was
  ever published. Rows carry `precinct='Electionwide'`; `n_precincts=0`.
- **2023 municipal primary: contest grain only** (official summary; no precinct
  report; portal doesn't carry it).
- **2025 (both elections): Enhanced Voting portal is the county's own linked
  official channel, but flags `isOfficialResults:false`** — no county canvass
  PDF exists. Portal precinct sums undercount summaries by 1–3 votes
  (unassigned bucket); the summary totals are used. **55 precinct-cells are
  published as null** (whole tiny precincts, e.g. 3LG21:CSD) — kept **blank**,
  never zero-filled.
- **2026 primary: the public precinct report withholds 36 of 126 precincts**
  (small-precinct privacy; 210 votes appear only in the summary). Withheld
  precincts stay absent; Electionwide rows carry the authoritative totals.
- **Vote-method split not extracted** — 2022 (Election Day/Absentee) and 2020
  presidential (Mail/Provisional) print method columns; only TOTAL is parsed
  (`vote_method='Total'` throughout). The split is recoverable from raw/.
- **`times_cast`/`registered_voters`** filled only on precinct-grain PDF rows
  (the block's own statistics); electionwide/portal rows leave them blank.
- **2021 primary Lewiston council: all four candidates printed as "CANDIDATE
  DISQUALIFIED"** (0 votes each, 231 undervotes in LEW01) — the county's own
  text, kept verbatim; aggregates to a single 0-vote by_contest row.
- Precinct id dialects are kept **verbatim per era** (2020 "Logan 01" /
  "College Young"; 2021–2023 "LOG24:CSD1"; 2026 "3LG24:CSD2"; portal
  "3LG21:CSD") — NOT reconciled to a single key (same stance as logan module).

## Honest gaps (verified absences — never filled)

- **2011, 2015, 2017, 2019 municipal: no county publication exists** (absent
  from the live page and archived versions — towns self-administered or
  cancelled; the county's municipal-canvass role lapsed between 2013 and 2021).
- **2021 general absentees:** Logan (self-run), Nibley (self-run RCV), Hyrum,
  Wellsville, Paradise, Clarkston, Cornish (cancelled or self-run — not
  determined; Utah Code 20A-1-206 cancellations leave no canvass).
- **2024 primary + general canvass reports are image-only scans** (no text
  layer) — catalogued + retained, not parsed; needs OCR/vision (queued).
- **2013 municipal:** per-precinct PDFs only (no countywide SOVC) — catalogued.
- **2010 general:** the county page publishes no result documents.
- **2006–2016 GEMS/SOVC era:** countywide SOVC PDFs mirrored + catalogued,
  not parsed (a different parser family; extension candidate). **2018:**
  inline-HTML results pages saved verbatim, not parsed.
- 2020 presidential primary has no summary report — precinct-grain only
  (internal totals plausible: Trump 12,978; Sanders 2,131 > Biden 874 on the
  March 3 ballot).

## Row counts / coverage (as built)

| File | Rows | Coverage |
|---|---|---|
| `cache_municipal_results_long.csv` | 2,107 | 2021 P (4 contests, 16 precincts) + G (25 contests, electionwide); 2023 P (4, electionwide) + G (16, 161 precinct blocks); 2025 P (8, 61 precincts + electionwide) + G (27, 85 precincts + electionwide) |
| `cache_county_office_results_long.csv` | 12,582 | 2020 presidential primary (85 precincts) / primary (84) / general (45 contests, 85 precincts); 2022 primary (165 precincts) / general (electionwide); 2026 primary (90 of 126 precincts + electionwide) — every contest in each document, verbatim |
| `election_results_by_contest.csv` | 285 (82 contests) | municipal council/mayor only, 18 Cache jurisdictions tagged; `logan` (held) = 34 rows |
