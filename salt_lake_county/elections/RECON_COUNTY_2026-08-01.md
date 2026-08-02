# RECON — Salt Lake County COUNTY-OFFICE (even-year) election results, 2026-08-01

Package A of the 2026-08-01 county-acquisition wave. Before this run the module held
the **odd-year MUNICIPAL canvass only**; the county's OWN offices — Mayor, the 9
Council seats, Sheriff, District Attorney, Clerk, Assessor, Recorder, Treasurer,
Auditor, Surveyor — had **zero result rows anywhere in the repo**. They now have a
canonical precinct-grain layer 2002–2026, a derived by-contest layer, and a STAGED
`election_race`-shaped promotion file.

Nothing in the odd-year municipal layer was touched: `slco_municipal_results_long.csv`,
`election_results_by_contest.csv` and `build_elections.py` are **byte-identical**
(verified with `git diff --stat`).

---

## 1. Channel inventory

Source of record: **Salt Lake County Clerk**,
<https://www.saltlakecounty.gov/clerk/elections/election-results/> (page read
2026-08-01). Everything acquired is catalogued row-by-row in **`sources.csv`**
(URL, election, role, format, bytes, **sha256**, retrieved date, acquisition
channel, notes). Binaries live under `raw/<year>/` and are gitignored repo-wide by
the `raw/` rule; `sources.csv` is what makes them re-fetchable.

| role | files | what it is |
|---|---:|---|
| `sovc` | 29 | precinct-grain Statement of Votes Cast / canvass workbooks, one per even-year election 2002–2026 (incl. the 2016 House-32 and 2024 CD-2 recounts) — **the parsed source** |
| `summary` | 31 | the county's certified summary / certification PDFs — **not parsed**; the independent cross-check channel |
| `cvr` | 1 | 2026 primary Cast Vote Record (ballot-level) — catalogued only, no loader |
| **total** | **61** | 208 MB |

Acquisition channels (`sources.csv.provenance`): **28 copied from the local mirror**
`~/Desktop/slco-election-archive` (byte-verified there by that archive's own
`download.py`; its `manifest.csv` supplied the authoritative saltlakecounty.gov URL
for each) and **33 fresh-downloaded from saltlakecounty.gov on 2026-08-01** — the
2026 primary (which postdates the mirror) and every summary PDF (which the mirror
never fetched). `acquire_county_raw.py` is idempotent and preserves each file's
original channel + date on re-run.

**1996 / 1998 / 2000 — the PDF-ONLY era.** All 5 even-year PDFs are mirrored and
catalogued and are **UNPARSED by design**: the county published no machine-readable
canvass before 2002. Their `sources.csv` rows say so explicitly.

**Publication gaps found while cataloguing** (verified against the county's own
listing page, not inferred):

- **2008 general — no summary PDF exists.** The county published the SOVC workbook
  only. The 5 county races of 2008 therefore have no independent cross-check.
- **2026 primary — the only PDF is a canvass STATISTICS report**
  (`combined-reports-for-website.pdf`: turnout, provisional and by-mail statistics,
  Clerk's certification signature). It carries no contest tallies, so the 2 county
  races of 2026 have no independent cross-check either.

Neither is a fetch failure and neither is filled in from anywhere else.

---

## 2. What parsed

`normalize_sovc_county.py` — the parser. Families **A / B / C / D are PORTED** (not
imported) from the proven upstream normalizer at
`~/Desktop/slco-election-archive/scripts/normalize_sovc.py`, carrying its 2026-07-19
fixes (`METHOD_LABELS` pseudo-candidate rejection, family-C suppressed-precinct
Total recovery, verbatim `Cumulative` rollup labelling). **The repo does not depend
on that Desktop path.** Families **E and G are new here** — the two even-year-only
layouts upstream never handled, including the **2002–2006 `.xls` canvass era the
upstream pipeline listed as "still unparsed"**. The 2020 SpreadsheetML pair (XML
wearing an `.xls` extension, likewise listed as unparsed upstream) is read by a
local SpreadsheetML reader and then parsed by the same family D.

**Every even-year workbook 2002–2026 parsed. There are no parse failures and no
approximations.**

| election | family | contests | of which county | long rows kept | reconciliation gate |
|---|---|---:|---:|---:|---|
| 2002-06-25 primary | G | 15 | 0 | 0 | exact 46 |
| 2002-11-05 general | G | 108 | 14 | 19,394 | exact 224 |
| 2004-06-22 primary | G | 13 | 0 | 0 | exact 36 |
| 2004-11-02 general | G | 96 | 8 | 10,459 | exact 266 + **2 known source discrepancies** |
| 2006-06-27 primary | E | 11 | 1 | 7,872 | exact 28 |
| 2006-11-07 general | A | 96 | 15 | 159,580 | exact 296 |
| 2008-06-24 primary | A | 12 | 0 | 0 | exact 57 |
| 2008-11-04 general | A | 85 | 5 | 34,652 | exact 283 |
| 2010-06-22 primary | A | 13 | 2 | 7,872 | exact 32 |
| 2010-11-02 general | A | 125 | 13 | 110,020 | exact 351 |
| 2012-06-26 primary | A | 12 | 2 | 11,584 | exact 29 |
| 2012-11-06 general | A | 84 | 6 | 27,968 | exact 271 |
| 2014-06-24 primary | A | 11 | 2 | 12,544 | exact 32 |
| 2014-11-04 general | A | 100 | 13 | 61,888 | exact 218 |
| 2016-06-28 primary | A | 22 | 0 | 0 | exact 95 |
| 2016-11-08 general | A | 123 | 6 | 29,335 | exact 292 |
| 2016-12-06 recount | A | 1 | 0 | 0 | exact 2 |
| 2018-06-26 primary | A | 7 | 0 | 0 | exact 17 |
| 2018-11-06 general | D | 95 | 10 | 12,008 | exact 220 |
| 2020-03-03 pres. primary | D | 2 | 0 | 0 | exact 21 |
| 2020-06-30 primary | D | 15 | 3 | 868 | exact 40 |
| 2020-11-03 general | D | 99 | 9 | 10,524 | exact 227 |
| 2022-06-28 primary | C | 18 | 1 | 662 | exact 43 |
| 2022-11-08 general | C | 100 | 8 | 9,057 | exact 211 |
| 2024-03-05 pres. primary | C | 1 | 0 | 0 | exact 6 |
| 2024-06-25 primary | C | 28 | 4 | 9,258 | exact 97 |
| 2024-08-05 recount | C | 1 | 0 | 0 | exact 3 |
| 2024-11-05 general | C | 95 | 10 | 22,452 | exact 158 + **suppressed-deficit 156** |
| 2026-06-23 primary | C | 16 | 2 | 3,450 | exact 23 + **suppressed-deficit 29** |
| **total** | | **1,404** | **134** | **561,447** | **3,624 exact / 185 suppressed / 2 known** |

### Scope of the committed canonical

The all-contests parse (federal, state, judicial retention, school board, special
district and the municipal contests the even-year canvass also carries) is
**3,035,500 rows / 416 MB** — an order of magnitude over GitHub's 100 MB hard limit.
The committed canonical `slco_county_results_long.csv` is therefore the **Salt Lake
County-level scope this module exists for**: 134 contests / **561,447 rows / 78 MB**.

Nothing is silently dropped:

- **`contest_inventory.csv`** catalogues **all 1,404 contests** across every
  workbook — year, election, sheet, parser family, contest title, the county-office
  classification, candidate/precinct/row counts, total votes, and `retained` yes/no.
- **`reconciliation_county.csv`** carries the gate result for **all 3,811 candidate
  columns**, county-level or not.
- `python3 normalize_sovc_county.py --full` reproduces the complete 3.0M-row parse
  into `raw/slco_evenyear_all_contests_long.csv` (gitignored) from the retained raws.

⚠ **Size note for the publish gate:** 78 MB is under GitHub's 100 MB hard limit but
over its 50 MB warning threshold. The coordinator may prefer to gitignore it and
regenerate (2 minutes) — the raws + `normalize_sovc_county.py` + the two committed
audit CSVs make it fully reproducible.

---

## 3. Gates passed

### Gate 1 — internal reconciliation (hard, `washington_county/normalize_canvass.py` precedent)

For **every** parsed sheet and **every** candidate column, the sum of the emitted
precinct rows must equal the workbook's **own certified-total row**, exactly. Each
parser family reads that row from where its era prints it: family G from the
`[NNNN] <name> <total>` legend; E from the trailing countywide `Total` block;
A from the `Election Total` / Type=`Total` rows; B/D from the trailing `Total:`
row; C from the outermost `County - Total` / `Countywide - Total` rollup (never
`Cumulative - Total`). Result over **3,811 candidate columns**:

- **3,624 exact.**
- **185 `suppressed-deficit`** — all in 2024 (156) and 2026 (29), the two elections
  where the workbook prints `****` "Insufficient Turnout to Protect Voter Privacy"
  on low-turnout precinct cells. The precinct rows genuinely cannot sum to the
  certified figure; the deficit is recorded per column and the certified figure is
  what the races layer reports (see §4).
- **2 `known-source-discrepancy`**, allowlisted and documented in the parser:

  > **2004 general, "Salt Lake City School District 2"** (a school-board contest —
  > it never reaches the county-office deliverable). The workbook prints 15 precinct
  > rows (matching its own "Precincts Counted 15") and its legend certifies
  > **ALAMA ULUAVE 1,939 / J. MICHAEL CLARA 1,938**, but those 15 rows sum to
  > **1,937 / 1,934**. Verified 2026-08-01 against the county's own certified
  > summary PDF (`2004-11-02-general-election.pdf`: "ALAMA ULUAVE 1939 50.01% /
  > J. MICHAEL CLARA 1938 49.99%") — the contest-level figure is the county's
  > certified one, so the 5 unallocated votes are a **source-internal contradiction,
  > not a parse loss**. Both figures are the county's own publication; the precinct
  > rows are kept **verbatim** and the contest total is not back-filled.

The run **exits 1** on any unallowlisted mismatch.

### Gate 2 — external cross-check against the county's certified PDFs

`verify_against_certifications.py` re-checks every staged race against a **second,
independently published county document** (the certified summary / certification
PDF for that same election, mirrored `role='summary'`), requiring a joint
name + exact-vote-count hit. **This is far beyond the "≥3 known outcomes per
decade" bar — it is every race that has a PDF to check against.**

| result | races | |
|---|---:|---|
| `match` | **115** | winner + winner_votes found in the county's own PDF |
| `no-pdf` | 5 | 2008 general — the county published no summary PDF |
| `no-contest-results` | 2 | 2026 primary — the PDF is a canvass statistics report |
| **NOT FOUND** | **0** | |

Per-year: 2002 12/12 · 2004 6/6 · 2006 13/13 · 2010 14/14 · 2012 7/7 · 2014 14/14 ·
2016 5/5 · 2018 10/10 · 2020 12/12 · 2022 9/9 · 2024 13/13. Full ledger:
`verification_county.csv`.

A **stricter machine check of the entire 2024 general** against
`2024-general-election-certification.pdf` (candidate-level and contest-total level)
came back **21/21 candidate figures exact and 9/9 contest totals exact** — e.g.
County Mayor Wilson 273,227 / Rider 224,325, total 497,552.

Historical coherence also holds independently: the At-Large seats fall on the
correct 6-year stagger (A 2002/2008/2014/2020, B 2004/2010/2016/2022,
C 2006/2012/2018/2024), districts 1/3/5 on midterms and 2/4/6 on presidential years,
and the parse independently surfaces the **2018 Recorder special election** for the
term Gary Ott left in 2017 (Recorder appears in both 2018 and 2020).

---

## 4. The layers

```
raw/<year>/…                     61 mirrored files (gitignored) + sources.csv catalog
acquire_county_raw.py            raw mirror + sources.csv (idempotent)
normalize_sovc_county.py         raw → canonical long + gate + inventory
county_contest_map.py            the county-contest classifier (shared, so it can't drift)
slco_county_results_long.csv     CANONICAL 561,447 rows, precinct x candidate x method
contest_inventory.csv            all 1,404 contests catalogued, retained yes/no
reconciliation_county.csv        the gate ledger, all 3,811 candidate columns
build_county_elections.py        canonical → the two derived layers
county_results_by_contest.csv    DERIVED 338 rows, contest x candidate
county_races.csv                 STAGED 122 races, the 25-col election_race shape
verify_against_certifications.py external PDF cross-check
verification_county.csv          its ledger
```

**`slco_county_results_long.csv`** keeps the workbook verbatim: contest title,
candidate string, precinct id, vote-method label, `suppressed` flag, `times_cast`,
`registered_voters`, plus `election_date` and the parser `family`. Its first 13
column names/order match `slco_municipal_results_long.csv` so the odd- and even-year
layers stay comparable.

**`county_results_by_contest.csv`** (338 rows) sums votes across precinct and method
per contest × candidate, and carries **three columns the municipal layer does not**:
`certified_votes` (the workbook's own contest-total row for that candidate),
`votes_basis` (`exact` on 314 rows, `suppressed-deficit` on 24), and
`election_date`. `votes` remains the precinct sum (the `election_result`
convention); where the two differ, `certified_votes` is authoritative.

**`county_races.csv`** — **STAGED, NOT FEDERATED.** 122 races in the uniform 25-column
`election_race` shape (SCHEMA_SPEC §9 order, ready for the loader). 105 general +
17 primary. Per office: Council 60, Auditor 8, Mayor 7, Assessor 7, DA 7, Recorder 7,
Sheriff 7, Surveyor 7, Clerk 6, Treasurer 6.

Confidence conventions, all carried in the row's own `note`:

- **Vote figures are the county's CERTIFIED totals**, not precinct sums, wherever the
  workbook printed a contest-total row (all 122 races). This is what makes the 2024
  and 2026 rows agree with the certification PDF to the vote.
- **17 primary rows are labelled** `PRIMARY: this is the party ballot's plurality
  leader (the nominee), NOT an election winner`. Party primaries are separate
  contests per party (e.g. 2020 Council District 6 has a DEM and a REP row).
- **7 rows are `uncontested='true'`** — a single candidate on the canvass.
- **2 rows carry an explicit `AUDIT FLAG`**: 2006 Surveyor and 2016 Council District 2,
  where the canvass's aggregate **write-in bucket** ("WRITE-IN", "WRITE-IN (NON)")
  is the runner-up, so `runner_up` / `margin_*` are measured against a write-in total
  rather than a named opponent. Do not quote those margins as a two-candidate result.
- The 2004 general **"Write-In for SL County Mayor"** contest — a write-in tally
  addendum the canvass prints beside the real mayoral race — is kept in the
  by-contest layer and **excluded from the races file** (it is not a race).
- **County ballot measures** (11 contests: the county propositions/proposals and the
  2024 jail bond) are kept in the by-contest layer with `office='Ballot Measure'`
  and excluded from the races file (no winner in the `election_race` sense).
- `n_seats` is blank in every workbook that does not print "(Vote for N)"; every
  Salt Lake County office in this file is single-seat, so it is set to 1 with a note.
- `total_first_choice_votes` is blank everywhere — **no county race has ever been RCV**.
- `registered_voters` is populated on all 122 rows; `ballots_cast` / `turnout_pct`
  only on the 42 rows whose workbook prints ballots per precinct (families C, E, G —
  families A and D print no per-precinct ballots-cast, so those stay blank). Where present they reproduce the workbook's own
  countywide header exactly (e.g. 2002: 435,575 registered / 226,022 cast).

---

## 5. Honest gaps and ceilings

1. **1996 / 1998 / 2000** — PDF-only era, mirrored and catalogued, **unparsed by
   design**. No machine-readable canvass exists.
2. **2008 general has no county summary PDF**; **the 2026 primary's PDF carries no
   contest tallies.** Those 7 races are internally gate-verified but have no
   independent second source.
3. **Privacy suppression 2024/2026.** 185 candidate columns lose votes to `****`
   precinct cells. The races layer reports the certified figures, so it is unaffected;
   the precinct-grain `votes` in `county_results_by_contest.csv` is short by the
   suppressed amount and says so in `votes_basis`.
4. **The 2004 school-district source-internal contradiction** (§3) — documented,
   allowlisted, never smoothed over.
5. **2002/2004 name clipping.** The 2002 GENERAL canvass overflows its name column,
   printing the certified total *inside* the name cell and clipping the party suffix
   (`AARON D. KENNARD RE121,314` → candidate `AARON D. KENNARD RE`, total 121,314).
   The clipped suffix is the county's own printing and is kept **verbatim**; the
   split is exact (every one of those columns reconciles).
6. **2002 `CANDIDATE WITHDREW` placeholders** (5 rows) have no code and no data
   column: the workbook records a withdrawal, nothing is invented for it.
7. **Party is only as good as the source.** 2018 and 2020 print no party at all;
   `party` is blank for those years rather than inferred.
8. **`district='At-Large'` without a seat letter** in the 2010 primary — the primary
   title omits the letter the general prints. Recorded as the source has it.
9. **The 2026 primary CVR is catalogued but not loaded** (as with the 2025 municipal
   CVR — a future ballot-level loader).

---

## 6. Not done here (for the coordinator)

- **Federation.** `county_races.csv` and `county_results_by_contest.csv` are staged
  only. `scripts/build_cities_db.py` needs loader extensions (see the handoff notes
  in the final report) — no shared script was touched by this package.
- The 4 remaining columns of `election_race` semantics that only a federated build
  can check (`county` back-reference, `gov_level`) are the loader's job.
