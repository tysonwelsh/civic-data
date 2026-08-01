# election_results — South Salt Lake City municipal elections

South Salt Lake City (**Salt Lake County**, Utah) municipal **general + primary** election
results, normalized to the SLC/South-Jordan sibling schema. Three CSVs + a reproducible
build script (`clean_elections.py`) + the retained raw county sources under `raw/`.
**Do not edit the CSVs by hand — regenerate** (see "Rebuilding"). Built 2026-07-12.

## Council / mayor structure

South Salt Lake is a **Council–Mayor (strong-mayor)** city: a **7-member council =
5 geographic DISTRICTS (1–5) + 2 AT-LARGE seats**, plus a **separately elected executive
Mayor** (citywide, non-voting on council). 4-year staggered, non-partisan terms, so each
odd-year cycle fills only part of the body:

| Cycle | Seats up | Years |
|---|---|---|
| **A** | **Mayor + one At-Large + District 2 + District 3** | 2009, 2013, 2017, 2021, 2025 |
| **B** | **the other At-Large + District 1 + District 4 + District 5** | 2007, 2011, 2015, 2019, 2023 |

There are **two physical At-Large seats** (one on each cycle), but the county labels do
**not** distinguish them, so both normalize to the single canonical contest
**`South Salt Lake City Council At-Large`** — the **year** disambiguates which seat. The
county label style drifts across years (`SOUTH SALT LAKE COUNCIL AT LRG` / `… CNCL @ LRG` /
`CITY OF SOUTH SALT LAKE COUNCIL AT-LARGE` / `… COUNCIL DISTRICT 2` / `… CNCL 3`); all are
canonicalized by `canon()`. (2007/2009 predate the At-Large-on-both-cycles pattern being
fully visible in the county data — 2007 is B with an At-Large; 2009 A shows no At-Large
contest.)

### The 2025 At-Large 2-year SPECIAL (kept distinct)
2025 ran an off-cycle **`At-Large (2-Year Term)`** special (`district='At-Large-2yr'`,
contest `South Salt Lake City Council At-Large (2-Year Term)`) to fill the **unexpired
remainder of Natalie Pinkney's At-Large term** — Pinkney (At-Large winner 2019 & 2023) was
**elected to the Salt Lake COUNTY Council in Nov-2024** and left the seat; **Ray deWolfe was
appointed Jan-2025** and then won the 2025 special (2,183–959 vs Conrad Campos). It is kept
as its **own contest** so member-term logic does not misread it as a cycle shift. (Verified
via the *South Salt Lake Journal*, 2025-02-28.)

## Source

All results are **Salt Lake County Clerk** SOVC (Statement of Votes Cast) data from the
local county mirror `~/Desktop/slco-election-archive` — **not re-scraped**. Two provenance
layers are retained here under `raw/`:

1. **`raw/municipal_results_long_south_salt_lake.csv`** — the repo-root canonical SOVC
   normalization (`salt_lake_county/elections/slco_municipal_results_long.csv`) filtered to
   `'SOUTH SALT LAKE'` (3,397 rows). Precinct- and vote-method-level. Consumed **directly**
   for **2007, 2009, 2013, 2015, 2017** (+ their primaries) and the **2023 & 2025**
   generals — all **zero-suppression**, summing cleanly to contest totals.
2. **`raw/sovc/*.xlsx`** — the true county SOVC spreadsheets, re-parsed directly for the
   contests the normalized slice does not deliver (below).
3. **`raw/2021-general-election-ranked-choice-summary-report.pdf`** (added 2026-07-31) —
   the Clerk's *Official Final Ranked Choice Results* for the 2021 general. Not parsed
   (SSL needs no round arithmetic — see the RCV section); retained as the **proof SSL was
   a pilot city**, which is what explains the absent 2021 primary.

## The recovered / re-parsed contests

| Contest(s) | Why the slice missed / broke it | Recovery |
|---|---|---|
| **2011 general** (At-Large + D1/D4/D5) and **2011 primary** (D4) | **Absent** from the slice — the archive normalizer keyed the contest off the **sheet name** (`S Salt Lake City Coun N`), so a `%SOUTH SALT LAKE%` filter never matched. | Re-parsed `raw/sovc/2011-11-08-…xlsx` + `2011-09-13-…xlsx` (Type-layout: per-precinct `Total` sub-rows). |
| **2019 general** (At-Large + D1/D4/D5) and **2019 primary** (At-Large + D1/D4/D5) | **Absent** for the same reason — general sheets `SSL Council N`; **primary sheets named numerically `21`–`24`**. This is the gap flagged in `recon.md`. | Re-parsed `raw/sovc/2019-11-05-…xlsx` + `2019-08-13-…xlsx` (Family-A wide crosstab; sheet is South Salt Lake **iff its row-0 title cell names the city** — the numeric primary sheet names are page numbers and are ignored). |
| **2021 general** (Mayor + At-Large + D2 + D3) | Present in the slice but **privacy-SUPPRESSED** at the In-Person/Vote-By-Mail method split (102/168 cells `****`), destroying precinct totals. | Re-parsed `raw/sovc/november-2-2021-…xlsx` (Sheet42–45), whose per-precinct **`Total`** sub-rows are **not** suppressed. |

After recovery the final CSVs have **zero suppressed cells** and **every by-precinct sum
reconciles exactly to its by-candidate total** (build validates 0 mismatches).

## ⭐ Ranked-choice voting — the 2021 pilot (LABEL CORRECTED 2026-07-31)

South Salt Lake joined **Utah's 2021 Municipal Alternate Voting Methods (RCV) pilot**, so
**the entire 2021 municipal general was ranked-choice** — all four rows now carry
`voting_method='RCV'` (matching sibling SLCo-canonical cities sandy/bluffdale) with
`total_first_choice_votes` filled and an explanatory `note`. **Until 2026-07-31 they were
mislabelled `plurality` with a blank first-choice column** — a label defect that both
mis-described the contests and made the (correctly) absent primary look like an
acquisition gap. **No tally changed**, because for SSL **round 1 was decisive in every
2021 contest**:

| 2021 contest | Cands | Why round-1 decisive |
|---|---|---|
| **Mayor** | 3 | Wood **1,777** cleared the **1,526** majority threshold outright — the county report reads *"Tabulation status: All Positions Filled"* with **only a Round 1 column**, no elimination round. |
| At-Large · D2 · D3 | 2 each | A 2-candidate ranked contest cannot go past round 1, so the county published no round table (identical treatment to `CITY OF BLUFFDALE MAYOR` in the same report). |

Therefore **round 1 == first choice == the SOVC `Total` column**, and `winner`,
`winner_pct`, and `margin_*` are all **RCV-final-accurate here** — unlike Draper/Millcreek
2021, where the first-choice leader was NOT the RCV winner. **This city is safe to quote
directly.** Independent cross-check: the report's round-1 figures match this repo's
`by_candidate` rows to the vote and to the hundredth of a percent — Wood 1,777/58.24%,
Christensen 678/22.22%, Siwik 596/19.53%.

Source retained locally: **`raw/2021-general-election-ranked-choice-summary-report.pdf`**
(Salt Lake County Clerk, *Official Final Ranked Choice Results*, 21 pp.; SSL Mayor is
p.20). Set in `clean_elections.py`'s `RCV_2021` map — regenerate, never hand-edit the CSV.

## KNOWN GAPS (documented, never fabricated)

- **2011 & 2019 general/primary** — the two gaps `recon.md` flagged. **RECOVERED** from raw
  (above), not left as gaps.
- **2021 municipal PRIMARY — NEVER EXISTED (corrected 2026-07-17; RE-VERIFIED AT THE
  PRIMARY SOURCE 2026-07-31).** The original reading ("3 mayoral candidates → an Aug-2021
  primary was almost certainly held") was WRONG: SSL was in the **2021 municipal RCV
  pilot**, and the pilot **replaces the municipal primary**, so all 3 mayoral candidates
  advanced straight to the ranked general (audited here). Two independent proofs, both
  local:
  1. **Direct** — the Salt Lake County Clerk's *Official Final Ranked Choice Results, 2021
     General Election* (`raw/2021-general-election-ranked-choice-summary-report.pdf`)
     tabulates **`CITY OF SOUTH SALT LAKE MAYOR` on p.20 of 21**. SSL is unambiguously a
     pilot city. (The 2026-07-17 note asserted the pilot but cited no document; this is
     that document.)
  2. **Corroborating** — the county's ONLY 2021-primary publication
     (`2021-08-10-primary-election-results.pdf` in the slco-election-archive) carries just
     **6 contests — Herriman Mayor, Murray Mayor, Taylorsville D5, West Jordan At-Large,
     West Valley Mayor, West Valley D2 — every one of them a NON-pilot city**, and no SSL
     contest. The pilot/primary split is clean; nothing is missing.
  **Not an acquisition gap — a non-event.** Do not re-open this from the CF filings: they
  prove a 3-way *race*, which is exactly what the ranked general was.
- **2023 & 2025 municipal PRIMARY — true no-contest.** The archive normalized both years'
  primaries but they contain **no South Salt Lake sheet** (each seat drew ≤2 candidates → no
  primary triggered). Verified in raw. Not a data gap.
- **2007 municipal PRIMARY** — the 2007 primary SOVC has no South Salt Lake sheet (only
  SLC). No 2007 SSL primary.
- **SPECIAL BOND measures** (2011 `S Salt Lake Bond`, 2015 `SOUTH SALT LAKE SPECIAL BOND`)
  are **ballot questions, not council/mayor seats** → intentionally **EXCLUDED** from the
  races file (noted here for completeness).

## The three CSVs

- **`south_salt_lake_races.csv`** — one row per race (**52 races: 40 general + 12 primary**),
  the 25-column superset (header taken from South Jordan): `year, election_type, office,
  district, contest, contest_verbatim, n_seats, n_candidates, voting_method, total_votes,
  total_first_choice_votes, winner, winner_votes, winner_pct, runner_up, runner_up_votes,
  margin_votes, margin_pct, registered_voters, ballots_cast, turnout_pct, uncontested,
  suppressed_precincts, note, source_file`. `district` ∈ `1–5` / `At-Large` /
  `At-Large-2yr` / `''` (Mayor). `total_first_choice_votes` and `note` are populated **only
  for the four 2021 rows** (the RCV pilot — see below); blank everywhere else.
  `suppressed_precincts='False'` everywhere in the final data.
- **`south_salt_lake_results_by_candidate.csv`** — race × candidate (**142 rows**):
  `votes, pct, rank, is_winner`.
- **`south_salt_lake_results_by_precinct.csv`** — precinct × candidate (**1,176 rows**).
  Precinct IDs are `SSL###` for 2011→2025; older county-wide numeric IDs for 2007–2009.

## Name normalization

`norm_name()` normalizes each candidate name **alongside** the verbatim source (never
overwrites raw): collapses whitespace, strips the `(NP)`/`(NON)` non-partisan tag, drops the
leading `*` registered-write-in mark, and canonicalizes write-ins to `Write-in` /
`Write-in (unresolved)`. To join elections ↔ minutes votes, further strip case/suffixes
(minutes `all_votes.csv` names are mixed-case).

## Verification / external cross-check (2026-07-12)

- **Mayor Cherie Wood, 2025:** CSV **2,203–1,097 (66.76%)** vs Brittany Karzen. Independent
  *Salt Lake Tribune* (2025-11-04) reported **65.8%** on election night — the CSV is the
  **final canvassed** SOVC figure; the ~1-pt drift is the expected late-ballot canvass. ✓
- **Ray deWolfe:** CSV shows him winning **At-Large 2017** and the **2025 At-Large 2-Year
  special**. The *South Salt Lake Journal* (2025-02-28) independently confirms deWolfe won
  a term in **2017**, did not seek re-election, was **appointed Jan-2025** to Pinkney's
  vacated At-Large seat, then ran the 2025 special. ✓
- **Natalie Pinkney:** CSV shows her winning **At-Large 2019 & 2023**; the same source
  confirms she vacated to join the **Salt Lake County Council (Nov-2024)**. ✓
- **Cherie Wood tenure:** CSV shows Mayor wins **2009, 2013, 2017, 2021, 2025** ("16 years"
  per the Tribune). ✓
- Notable close races: **2013 Mayor** Wood +49 (1,008–959 vs Pehrson); **2017 Mayor** Wood
  +43 (1,524–1,481 vs Kindred); **2015 D5** Siwik +16; **2021 At-Large** Williams +95;
  **2023 D4** Mitchell +33 (unseating incumbent Portia Mila).

### ⚠ Elected-winner vs 2026-serving-roster discrepancies (roster follow-ups, NOT election errors)
The **elected** 2023 district winners differ from the **2026 serving** council at two seats
— consistent with post-election mid-term appointments (as happened at At-Large with
deWolfe):
- **District 1:** elected 2023 = **LeAnne Huff**; serving 2026 = **Joy Glad** (Glad never
  appears as an election winner in this data → appointed).
- **District 5:** elected 2023 = **Paul Sanchez** (uncontested); serving 2026 = **Irvin
  Jones** (Jones last *elected* to D5 in 2011 → returned by appointment).
These belong to the **roster layer**, not here — the election CSVs faithfully record who
was **elected**. Flag for `roster/` reconciliation.

## Rebuilding

```
cd election_results && python3 clean_elections.py            # reads raw/, writes the 3 CSVs
                       python3 clean_elections.py --report    # + per-race summary
```
Idempotent; asserts 0 by-precinct/by-candidate mismatches. Re-run only when a **new cycle**
posts: add its SOVC to the archive + `raw/sovc/`, then either refresh the archive slice (if
the normalizer covers the new year cleanly) or add a raw-parser call (mirror the
2019/2021 handling). Mind whether the cycle is A (Mayor+AL+D2+D3) or B (AL+D1+D4+D5).
