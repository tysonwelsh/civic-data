# salt_lake_county / elections — the canonical Salt Lake County canvass

**This is the county-level canonical source for Salt Lake County elections.** The 7 SLCo
cities in this repo (slc, sandy, west_jordan, west_valley, south_jordan, millcreek,
taylorsville) all draw from the *same* county-clerk canvass — this module holds it once,
at the level where it actually originates, instead of 7 divergent city copies.

**TWO layers, two election cycles, two canonical long files** (they never overlap):

| | ODD years | EVEN years |
|---|---|---|
| canonical | `slco_municipal_results_long.csv` | `slco_county_results_long.csv` |
| what | MUNICIPAL offices (every SLCo city/town) | the COUNTY's OWN offices + county ballot measures |
| span | 2007–2025 | 2002–2026 |
| derived | `election_results_by_contest.csv` | `county_results_by_contest.csv` |
| races | (city `<slug>_races.csv`, federated) | `county_races.csv` — **STAGED, not federated** |
| builder | `build_elections.py` | `normalize_sovc_county.py` → `build_county_elections.py` |
| status | federated into `gov.db` | **staged 2026-08-01, awaiting loader extension** |

## Files — the ODD-year municipal layer

- `slco_municipal_results_long.csv` — **canonical.** The Salt Lake County Clerk Statement
  of Votes Cast (SOVC), tidy long form: one row per precinct × candidate × vote-method,
  248,801 rows, 2007–2025, **every SLCo municipality** (not just the 7 held cities).
  Verbatim analysis layer — never hand-edit. Includes the **2019 municipal primary**
  (32 contests, recovered 2026-07-16 by the upstream `parse_family_d()` re-parse of the
  numbered-sheet/Table-of-Contents workbook era; verified exact vs 9 audited per-city
  races in bluffdale/midvale/riverton/south_salt_lake) and, since **2026-07-19**, the
  **2021 suppressed-precinct Total-recovery rows** (+3,090 `vote_method='Total'` rows in
  64 of 66 2021 contests): the 2021 workbook prints `****` on low-turnout precincts'
  method sub-rows but DOES print each precinct's own Total sub-row; the upstream
  family-C parser used to drop all Total rows, silently losing those votes (the cause
  of the SLC 2021 D2 "Palmer 363 / Puy 361" partial-count swap — certified first-choice
  totals are **Puy 1,084 / Palmer 751**). Recovery emits a Total row only where every
  method row for that candidate+precinct was suppressed (can never double-count);
  verified exact against 9 audited city races (murray/midvale/holladay) and the
  workbooks' own `Electionwide - Total` rows. All other years byte-identical.
  Since the same-day lead-(v) fix, the family-C sheets' trailing all-zero
  `Cumulative` report-template sections carry **`precinct='Cumulative'`** (the
  workbook's own rollup label) instead of being misattributed to each sheet's
  last real precinct — 638 rows (332 in 2021 general, 306 in 2023 general), all
  `votes=0`; treat `precinct='Cumulative'` as a rollup label, never a precinct
  (`build_elections.py` excludes it from `n_precincts`; the rebuilt by-contest
  file was byte-identical).
  **Pseudo-candidate residue fix (2026-07-19, same-day follow-up to lead (m)):** the
  2019 general **`ALT Council`** sheet (Alta Town Council — the ONLY affected contest,
  proven by full-archive candidate-name frequency analysis and a CUMULATIVE-header scan
  of every 2018/2019 workbook) used to carry **11 method-label pseudo-candidate rows**
  ("Vote Centers"/"Vote By Mail"/"Early Voting"/"Vote Center"/"Mail"/"Early"/"Total")
  instead of its candidates: the sheet's trailing CUMULATIVE header block made the
  family-B parser reject it (no `Total Votes` sub-column in the block), whereupon
  family A misread the method sub-header labels as candidates — emitting two real
  candidates' method SUBTOTALS plus the grand-total/cumulative columns as candidate
  rows and dropping SHERIDAN J. DAVIS (the actual leader) entirely. The upstream
  normalizer now exact-match rejects method/section labels at every candidate-detection
  site (`METHOD_LABELS` / `is_pseudo_candidate()`), letting family B parse the sheet
  correctly. Net −8 rows (−11 pseudo, +3 real: **DAVIS 77 / MORGAN 69 / LENCHES-JHAMB
  29**, cell-verified against the raw workbook; 77+69+29=175 = the workbook's own grand
  total). Every other row of the canonical is byte-identical and in identical order;
  the lead-(m) proofs (3,090 `vote_method='Total'` rows; slc 2021 D2 Puy 1,084/751;
  alta 2021 recovered Totals) and the lead-(v) proof (638 Cumulative rows) all re-ran
  clean, and all six re-pointed city pipelines rebuilt **byte-identical** (Alta's own
  floor is 2020, so the repaired 2019 contest lives only in this canonical + the
  by-contest file).
- `election_results_by_contest.csv` — **derived** (`build_elections.py`). One row per
  contest × candidate, votes summed across precinct + vote-method, **municipal
  council/mayor contests only** (the growth-relevant governance offices),
  `jurisdiction_slug`-tagged for the 7 held cities. This is what loads into the
  `gov.db` `election_result` table. (2026-07-19 Total-recovery rebuild: 143 of the
  2021 rows' `votes` corrected upward, 30 `rank_in_contest` changes — the 2021
  plurality leaders now agree with the audited per-city `_races.csv` winners
  everywhere, incl. slc D2 Puy, murray D2 Cotter, cottonwood_heights D3 Newell +
  Mayor Weichers, kearns D2 Peterson, sandy D1/At-Large first-choice leaders, and
  alta's previously all-suppressed at-large tallies. No rows added/removed.) (Same-day
  pseudo-candidate rebuild: the 7 `ALT Council` 2019 method-label rows became the 3
  real-candidate rows — Davis 77 now correctly `rank_in_contest=1`; all other rows
  unchanged, 2,172 total.)
- `build_elections.py` — regenerates the derived file from the canonical long file.
  Idempotent; DERIVED output, never hand-edited.
- `raw/SOURCES.md` — provenance + the upstream pipeline.

## Files — the EVEN-year COUNTY-OFFICE layer (added 2026-08-01, **STAGED**)

The county's own elected offices — **Mayor, the 9 Council seats (3 at-large A/B/C +
6 districts), Sheriff, District Attorney, Clerk, Assessor, Recorder, Treasurer,
Auditor, Surveyor** — are elected in EVEN years and had **zero result rows anywhere
in the repo** before this. Full record: `RECON_COUNTY_2026-08-01.md`.

- `slco_county_results_long.csv` — **canonical.** One row per precinct × candidate ×
  vote-method, **561,447 rows / 134 contests, 2002–2026**, verbatim. Columns match
  the municipal long file's first 13 with `election_date` + `family` inserted.
  Scoped to **Salt Lake County-level contests** (offices + county ballot measures);
  the full 1,404-contest parse (federal/state/judicial/school/municipal, 3.0M rows /
  416 MB) is over GitHub's limit and lives behind `--full` under gitignored `raw/`.
  **Nothing is silently dropped** — `contest_inventory.csv` catalogues all 1,404.
- `contest_inventory.csv` — every contest in every even-year workbook, with its
  county-office classification and `retained` yes/no. The proof of scope.
- `reconciliation_county.csv` — the **hard gate ledger**, all 3,811 candidate columns:
  precinct sum vs the workbook's own certified-total row. **3,624 exact**, 185
  `suppressed-deficit` (2024/2026 `****` privacy suppression), 2
  `known-source-discrepancy` (the 2004 SLC School District 2 contest — the county's
  own precinct rows and its own certified total disagree by 5 votes; kept verbatim,
  allowlisted, verified against the county's certification PDF).
- `county_results_by_contest.csv` — **derived**, 338 rows, contest × candidate.
  `votes` = precinct sum (the `election_result` convention); **`certified_votes`** =
  the workbook's own contest total, which is LARGER wherever suppression hid cells —
  `votes_basis` says which applies (314 exact / 24 suppressed-deficit).
- `county_races.csv` — **STAGED**, 122 races in the uniform 25-column `election_race`
  shape. Vote figures are the county's **certified** totals. ⚠ NOT federated:
  `scripts/build_cities_db.py`'s `load_election_race()` reads only `level=='city'`
  entities today. Read each row's `note`: 17 primary rows are a **party ballot's
  nominee, not an election winner**; 7 are uncontested; **2 carry an `AUDIT FLAG`**
  (2006 Surveyor, 2016 Council D2 — the canvass's aggregate write-in bucket is the
  runner-up, so those margins are not two-candidate margins).
- `acquire_county_raw.py` / `normalize_sovc_county.py` / `county_contest_map.py` /
  `build_county_elections.py` / `verify_against_certifications.py` — the pipeline,
  in that order. All idempotent; all outputs DERIVED, never hand-edited.
- `verification_county.csv` — the **external** gate: every staged race re-checked
  against the county's own certified summary PDF. **115 match / 0 NOT FOUND**;
  the 7 unchecked are honest publication gaps (no summary PDF exists for the 2008
  general; the 2026 primary's PDF is a canvass *statistics* report with no tallies).

**Parser lineage:** families A/B/C/D are **ported, not imported**, from
`~/Desktop/slco-election-archive/scripts/normalize_sovc.py` (the repo must never
depend on that path). Families **E (2006)** and **G (2002/2004 single-sheet canvass)**
are new here, and the 2020 SpreadsheetML pair is read by a local reader — those three
eras were listed as *"still unparsed"* upstream and are now parsed and gate-verified.

**Even-year quirks to respect:** the 2002 GENERAL canvass overflows its name column,
printing the total inside the name cell and clipping the party suffix
(`AARON D. KENNARD RE121,314`) — split exactly, suffix kept verbatim; 2018 and 2020
print **no party at all**; the 2010 primary prints `At-Large` with no seat letter;
2002 prints 5 `CANDIDATE WITHDREW` placeholders with no data column (nothing invented).

## Provenance

Source for both layers: **Salt Lake County Clerk** —
<https://www.saltlakecounty.gov/clerk/elections/election-results/>.

- **ODD-year municipal:** ingested + normalized by the personal pipeline at
  `~/Desktop/slco-election-archive` (`raw/` verbatim mirror →
  `scripts/normalize_sovc.py` → `data/municipal_results_long.csv`, copied here). Its
  raws are **linked, not re-hosted**. Re-fetch there before each election.
- **EVEN-year county-office:** raws are **mirrored in this module** at `raw/<year>/`
  (61 files / 208 MB, gitignored by the repo-wide `raw/` rule) and catalogued with
  URL + bytes + **sha256** + acquisition channel in **`sources.csv`** — 28 copied
  from the local mirror, 33 fresh-downloaded from saltlakecounty.gov on 2026-08-01.
  Refresh with `python3 acquire_county_raw.py` (idempotent; preserves each file's
  original channel and date), then rerun `normalize_sovc_county.py` →
  `build_county_elections.py` → `verify_against_certifications.py`.

## How the cities relate (the tier)

Each city's `election_results/<slug>_races.csv` is a **filtered, audited slice** of this
canvass (verified: the county derivation reproduces SLC's audited 2023 winners and vote
counts exactly). In `gov.db`:

- `election_race` (city grain) = the 16 cities' audited race summaries — **authoritative
  winners/margins**. View: `v_election_city` (races + containing county).
- `election_result` (county grain) = this module's candidate tallies. `rank_in_contest`
  is **plurality** order — for RCV cities (millcreek 2021/2023) the RCV final winner
  differs; always take winners from `election_race`.

## Known publication limits of the county canvass (verified 2026-07-16 — honest gaps, NOT parse failures)

- **2021 municipal primary: the county published NO SOVC workbook** — only a 1-page
  election-night contest summary PDF (6 contests county-wide; archived at the upstream
  mirror `raw/2021/2021-08-10-primary-election-results.pdf`). It is contest-grain, not
  precinct-grain, so it is NOT loaded into this canvass. The small contest count is real:
  the 2021 RCV-pilot cities (incl. south_salt_lake) held no primary at all, and Murray's
  D4 field dropped to 2 before certification. The Herriman + Murray MAYOR primaries exist
  only in that PDF.
- **Cancelled (uncontested) elections leave no canvass** — Utah Code 20A-1-206: Magna's
  Nov-2023 council election (D1/D3/D5; Resolution 2023-09-02 — Prokopis/Sudbury/Pierce
  deemed elected) and Alta's Nov-2025 general (Resolution 2025-R-26 — Bourke/Anctil/
  Heimark deemed elected) were cancelled; their absence from the SOVC is correct.
- ~~Still unparsed upstream: 2020 primary + 2020 presidential primary (SpreadsheetML
  `.xls`), the 2002–2006 canvass era…~~ **CLOSED 2026-08-01** by the even-year build:
  the 2002/2004 single-sheet canvasses (family G), 2006 (family E) and the three 2020
  SpreadsheetML workbooks (local XML reader → family D) all parse and pass the
  reconciliation gate. Still unparsed, honestly: the **1996/1998/2000 PDF-only era**
  (no machine-readable canvass exists — mirrored + catalogued only) and the **Cast
  Vote Records** (2025 municipal, 2026 primary — ballot-level; future loader).

## Not done yet (tracked in root TODO.md)

**The even-year county-office layer is STAGED, not federated (2026-08-01).**
`scripts/build_cities_db.py` needs two loader extensions before `county_races.csv` and
`county_results_by_contest.csv` reach `gov.db`: `load_election_race()` currently
iterates `level=='city'` only, and `load_election_result()` reads only each county's
`election_results_by_contest.csv`. Until then, query the CSVs here directly — and note
that `election_result`/`election_race` in `gov.db` still contain **odd-year municipal
rows only** for Salt Lake County.

The 3 city pipelines still parse their own raw (SLC filters county per-year CSVs;
sandy/wj/wvc parse per-city SOVC `.xlsx`; sj/millcreek/taylorsville use city long-slices).
Mechanically re-pointing all 7 to filter *directly* from this canonical file (byte-identical
output) is a deferred follow-up — the lineage is proven and documented; the value
(canonical county source + DB form) is delivered.
