# summit_county / elections — VERIFICATION

Build date: 2026-07-20. Builder: `build_elections.py` + `canvass_parsers.py`
(idempotent; every gate below is re-asserted on each run — reconciliation
failures raise and abort the build).

## Verification architecture (three independent gates)

1. **Summary internal gate** — in every machine-readable Summary Results
   Report, the per-contest candidate sums must equal the printed
   `Total Votes Cast` (Electionware/table eras) or `Total Votes` (GEMS era).
   **209 EW/table contests + 195 GEMS-summary contests: 0 mismatches.**
2. **Precinct↔certified cross-document gate** — the precinct-grain layer,
   summed per contest × candidate, must equal the certified summary layer
   exactly, up to (a) precinct suppression (2024+ reports print `Suppressed`
   on low-turnout precincts — deltas allowed only downward and only on
   contests with suppressed rows; full delta ledger below) and (b) write-in
   presentation (precinct reports print one `Write-In Totals` line; summaries
   allocate named sub-lines — compared as aggregates).
3. **GEMS in-document gate** — the GEMS SOVC prints its own jurisdiction-wide
   `Total` group per contest; the precinct×method rows must sum to it
   exactly. **All 14 GEMS SOVC files: 826 contest×candidate totals, 0
   mismatches.**

## Per-election results

| Election | Precinct source | Certified source | Gate | Result |
|---|---|---|---|---|
| 2006 general | GEMS SOVC (flat, 41 precincts) | SOVC Total rows | 3 | PASS 90/90 |
| 2008 WSPP / primary / general | GEMS SOVC | SOVC Total rows | 3 | PASS 7+10+129 |
| 2010 primary / general | GEMS SOVC | SOVC Total rows | 3 | PASS 12+103 |
| 2011 municipal general | — (see gaps) | GEMS summary | 1 | PASS 10 contests |
| 2012 primary / general | GEMS SOVC | SOVC Total rows | 3 | PASS 27+97 |
| 2014 primary (PC#5+SS#4) | GEMS SOVC ×2 | SOVC Total rows | 3 | PASS 4+3 |
| 2014 general | GEMS SOVC (EV+ED only) | GEMS summary | 1+3 | PASS (see gaps) |
| 2015 municipal general | GEMS SOVC | SOVC Total rows | 3 | PASS 35/35 |
| 2016 primary / general | GEMS SOVC | SOVC Total rows | 3 | PASS 21+92 |
| 2018 primary | EW precinct pages | EW summary | 1+2 | PASS 9/9 |
| 2018 general | EW precinct pages | precinct-sum (summary is a scan) | vision | 7/7 county contests EXACT (below) |
| 2019 municipal general | EW precinct pages | EW summary | 1+2 | PASS 19/19 |
| 2020 pres. primary | EW precinct pages | precinct-sum (summary is a scan) | vision | internally exact; 1-vote doc-level delta (below) |
| 2020 primary / general | EW precinct pages | EW summary | 1+2 | PASS 21+111 |
| 2021 municipal primary | EW precinct pages | EW summary | 1+2 | PASS 32/32 |
| 2021 municipal general | crosstab city reports | EW summary (per-section) | 1+2 | PASS 38/38 |
| 2022 general | precinct table | table summary | 1+2 | PASS 91/91 |
| 2023 mun. primary / general | precinct tables | table summaries | 1+2 | PASS 23+29 |
| 2024 pres. primary / general | precinct tables | table summaries | 1+2 | PASS 5+120 (suppression-aware) |
| 2025 mun. primary / general | precinct tables | table summaries | 1+2 | PASS 27+36 (suppression-aware) |
| 2026 primary | precinct table | table summary | 1+2 | PASS 8/8 (suppression-aware) |

## Park City in the county canvass — VERDICT: YES, fully

Park City self-administers its municipal elections (the city's Board of
Canvassers certifies), but the Summit County Clerk tabulates under contract
and **publishes Park City's contests inside the county canvass at precinct
grain** — verified in the documents' bodies for 2011, 2015, 2019, 2021
(primary+general), 2023 (primary+general) and 2025 (primary+general),
including the 11 Park City precincts' per-precinct tallies.

Cross-check against the audited city layer
(`park_city_city_council/election_results/park_city_results_by_candidate.csv`,
READ-ONLY): **49 of 50 candidate rows 2019–2025 match EXACTLY** (incl. the
2025 mayor 1,706/1,699 recount values); the 50th is the county's `Withdrawn`
0-vote ballot line (2021 general), which the city layer legitimately omits.
The future per-city re-point (separately queued, byte-identity-gated) is
viable on this evidence.

## Suppression ledger (never imputed)

321 suppressed precinct-row cells across 4 elections (2024 general: precincts
COLN56:10, PRM48:N5B, WNW17:P4B; 2025 mun. primary; 2025 mun. general:
22PRM:8A, 22SCRU:8, 22DVS:30 et al.; 2026 primary). They carry `votes=''`,
`suppressed=True` in the long file. Governance-contest deltas
(certified − precinct-visible), all attributable to suppressed precincts:

- 2024 county offices (Assessor/Recorder/Sheriff/Treasurer/Council A–C):
  6–8 votes each.
- 2025 Park City Mayor: Rubin −4 (Dickey 0); 2025 Park City Council
  (primary+general): 1–3 votes per candidate; suppressed precinct 22DVS:30.

Note the two Totals-row vintages: 2025-style precinct tables **exclude**
suppressed precincts from their own Totals row; 2024-style **include** them.
The parser verifies against whichever the document uses; certified values in
`election_results_by_contest.csv` always come from the Summary Report.

## Vision spot-checks of the two scanned summaries

- **2018 general** (`2018_general_summary.pdf`, scan): pages 4–6 read
  visually. All 12 checked values EXACT vs the precinct-derived totals, incl.
  every county office: Council Seat D 14,417; Seat E Wright 13,467 +
  Write-In Totals 1,360; Attorney 14,345; Auditor 14,269; Clerk 14,627;
  Recorder/Surveyor 14,471; Sheriff 15,019. The scan additionally allocates
  Seat E write-ins by name (Write-In: Josh Mann 1,159 / Not Assigned 201) —
  available only in that scan; the machine layer carries `Write-In Totals`.
- **2020 presidential primary** (`2020_pres_primary_summary.pdf`, scan):
  both contests read visually; vision sums equal the printed Total Votes Cast
  exactly (DEM 6,938; REP 4,024). **One document-level disagreement:**
  certified summary prints BLOOMBERG **1,652**; the official precinct report
  sums to **1,651** (independently re-summed from raw text: 1,651 across 51
  precincts). The 1-vote delta is between the county's own two official
  documents; the long file is faithful to the precinct report and this note
  is the record. (Federal contest — not in the by-contest governance layer.)

## Honest gaps (none imputed, all catalogued in sources.csv)

- **2004 general**: precinct report is a text-less scan (8 pp). Catalogued,
  not normalized. No summary published.
- **2006 primary**: the archive row's link (`DocumentCenter/View/345`)
  serves the **2010 primary SOVC** (byte-identical to the 2010 file;
  body-verified "June 22, 2010"). County mis-link; 2006 primary results are
  a genuine gap.
- **2005, 2007, 2009, 2013, 2017 municipal elections**: absent from the
  county archive entirely — municipalities self-administered odd-year
  elections in that era (the county page says to contact each municipality).
  Structural, not a retrieval failure.
- **2019 primary**: the archive row shows dead "View Report" labels with no
  hyperlinks. Not recoverable from this channel; EV portal does not reach
  back to 2019.
- **2021 GO bond standalone pair** (`2021_go_bond_*.pdf`): retained; content
  duplicates the Open Space Bond section of `2021_general_precinct.pdf`
  (which is what the build parses) — parsed values reconcile against the
  County GO Bond Summary Report section (12,732-vote contest, PASS).
- **2011 municipal general precinct grain**: the SOVC prints precinct GROUPS
  WITHOUT their name labels on municipal contest pages (verified in body:
  method rows under "Jurisdiction Wide" with no precinct headers). Loading
  unnamed groups would require inventing precinct identities — refused.
  Contest grain (from the clean GEMS summary) is loaded; the write-in
  horizontal-continuation pages (12/14/16) are part of the same limitation.
- **2014 general precinct grain is partial by the report's own statement**:
  "precinct results for Early Voting and Election Day [only]; paper ballots
  … not included". Long-file rows are those partial methods (honest);
  certified by-contest totals come from the complete GEMS summary.
- **2015 HENEFER**: the SOVC prints an all-zero two-write-in-column contest
  (no votes recorded anywhere, including its Total rows). Excluded from the
  normalized layer as a source artifact; Henefer's 2015 outcome is not
  recoverable from this canvass.
- **2015 / 2016 summaries**: garbled scans (OCR-broken digits). Certified
  totals for those years come from the SOVCs' own jurisdiction Total rows
  (gate 3).
- **2022 primary**: all three documents (summary, 111-pp precinct report,
  116-pp certified canvass packet) are image-only scans with no text layer.
  Catalogued + retained; normalization deferred (OCR pass queued).
- **2024 June regular primary**: absent from BOTH the county archive page
  (its "Primary" row serves an unofficial copy of the March presidential
  primary — body-verified) AND the county's Enhanced Voting portal election
  list. Not published on any county channel found; genuine gap.
- **2026 primary canvass packet**: signed/scanned packet (retained,
  catalogued); the machine-readable official summary+precinct reports are
  the parsed sources. The 2026 CVR is an XLSX served with a `.pdf`-less
  content type — retained as `2026_primary_cvr.xlsx` (ballot-level; future
  loader).

## Cross-check channel

The Utah Enhanced Voting portal API
(`electionresults.utah.gov/results/public/api/…/summit-county-ut/…`) covers
2023-09 → 2026-06 (7 elections) and is retained verbatim as `raw/ev_*.json`
(cross-check only; the certified PDFs are canonical). Spot-verified: EV 2025
general Coalville Mayor WOOD 251 / SWENSEN 276 equals the certified summary.
