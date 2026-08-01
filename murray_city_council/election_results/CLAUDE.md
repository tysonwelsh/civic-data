# election_results — Murray City municipal elections

Murray City (**Salt Lake County**, Utah) municipal **general + primary** election results,
normalized to the SLC/Sandy/south_jordan sibling schema. Three CSVs + a reproducible build
script (`clean_elections.py`) regenerates the 2021/2023/2025 cycles. Original data floor
**2020**; **six 2019/2021 rows were hand-appended 2026-07-17** from the SLCo SOVC re-parse
(owner-approved — the 2019 general D1/D3/D5, 2019 primary D1/D3, and the 2021 MAYOR primary;
see the dated note at the end of this file). Those recovered rows are NOT reproduced by
`clean_elections.py` and must be re-appended if the file is regenerated.

## Council / mayor structure

Murray is a **Council–Mayor** city: a **5-member council, each seat elected by
single-member DISTRICT (D1–D5)**, plus a **separately elected Mayor** (citywide; the mayor
is executive and does **not** vote on the council). 4-year staggered terms:

| Cycle | Seats up | In-scope years |
|---|---|---|
| **A** | **Mayor + District 2 + District 4** | 2021, 2025 |
| **B** | **Districts 1, 3, 5** | 2023 |

Mayor sits only on the **A** cycle → **no mayor race in 2023**. **2025 additionally held a
`District 3 (2-Year Term)` unexpired-term SPECIAL** (off the normal B-cycle — D3's regular
seat is a 2023/2027 seat; the 2-year special fills the balance of the term after mid-term
D3 churn). It is flagged in the `note` column and its canonical `contest` keeps the
`(2-Year Term)` marker so it never collides with a regular D3 race.

## Source (single canonical provenance)

All results are filtered from the **county-canonical** normalized Statement-of-Votes-Cast
(SOVC) long file — **not re-scraped**:

    /Users/tysonwelsh/civic-data/salt_lake_county/elections/slco_municipal_results_long.csv

**Filter:** rows whose `contest` contains `MURRAY` (case-insensitive), `year ∈ {2021,2023,
2025}`. Each source row is precinct- and vote-method-level and carries the true
`source_file` + `sheet`. No local `raw/` mirror of the **county** SOVC is kept — the county repo
is the source of record. **One exception (2026-08-01):** `raw/` holds Murray's own certified
**2021 primary Board of Canvassers' Report** (city docid 12340), a CITY document the county
layer does not carry — it is the source for the 2021 Mayor-primary row's turnout fields and the
proof that no D4 primary was held. Rebuild: `python3 clean_elections.py [--report]` (idempotent).

### Two dedup / recovery decisions (both material)

1. **UPPER-CASE vs Mixed-Case "duplicate" labels are the GENERAL vs the PRIMARY** — not two
   copies of one race. In 2023 the file carries both `MURRAY CITY COUNCIL DISTRICT 1`
   (general, `…official-report-12-05-2023….xlsx`) and `Murray City Council District 1`
   (primary, `statementofvotescastrpt.xlsx`), with different candidate sets. Keying every
   race on **(year, election_type, canonical_contest)** keeps them distinct — no merge.

2. **The 2023 PRIMARY rows are triplicated** — the primary sheets export each
   `precinct × candidate` row **three times, verbatim** (a county-file artifact). Left
   un-deduped this triples the primary totals (D1 primary would read 1 584 instead of 528).
   The build **collapses rows identical across every field** before summing. This is safe
   against genuine **boundary-split precincts** (e.g. 2023 general `MUR047`, which straddles
   a district line and appears as two *differing* partial rows) — those differ in votes or
   `times_cast`, so they are **not** collapsed and still sum correctly. There are **no
   "Total"/"Cumulative" precinct rows** in the file (all precincts are `MUR###`), so the
   only double-count risk was the triplication.

3. **2021 general recovered from the raw SOVC workbook.** In the long file the 2021 general
   exists only at the In-Person / Vote-By-Mail method split, and the small In-Person cells
   are **privacy-suppressed** (`****`): D2 100 % suppressed, D4 20/36 rows, Mayor 152/208
   rows. Summing only the surviving cells would publish a gross undercount (Mayor Hales
   would read **983**, not the true **6 108**). The un-redacted per-precinct **`Total`**
   sub-rows live in the raw county SOVC workbook, already mirrored **locally** (not
   re-downloaded):
   `~/Desktop/slco-election-archive/raw/2021/november-2-2021-general-election-statement-of-votes-cast.xlsx`
   (Sheet24 Mayor, Sheet25 D2, Sheet26 D4). The 2021 general is parsed from those `Total`
   rows — same county SOVC provenance chain, just the totals the method-split destroys.
   This is the identical method the sibling `south_jordan` build documents for its own 2021.
   After recovery, **no race carries `suppressed_precincts=True`** and every by-precinct sum
   reconciles exactly to its by-candidate total (verified: 0 mismatches).

## The three CSVs

- **`murray_races.csv`** — one row per race (**21 races: 13 general + 8 primary** after the
  2026-07-17 SOVC-reparse appends; was 15), the
  25-column SCHEMA_SPEC superset (identical header to `south_jordan_races.csv`), incl.
  `total_first_choice_votes` (blank — Murray is plurality, **no RCV**), `winner`/
  `winner_votes`/`winner_pct`, `runner_up`/`runner_up_votes`, `margin_votes`/`margin_pct`
  (= winner − runner-up), `registered_voters`/`ballots_cast`/`turnout_pct` (populated for
  all in-scope races), `uncontested`, `suppressed_precincts` (**False everywhere** after
  recovery), and `note` (special-election + any suppression flags).
- **`murray_results_by_candidate.csv`** — race × candidate (**47 rows**): `votes`, `pct`,
  `rank`, `is_winner`.
- **`murray_results_by_precinct.csv`** — precinct × candidate (**909 rows**), precinct IDs
  `MUR###`; `suppressed` column (all `False` in the final data).

## Name normalization

`norm_name()` normalizes each candidate **alongside** the verbatim value: collapses
whitespace, drops the leading `*` write-in mark, strips the `(NP)`/`(NON)` non-partisan
tag, and canonicalizes write-ins to `Write-in` / `Write-in (unresolved)`. Election names
are **UPPER-CASE**; to join elections ↔ council votes/roster, match on **person + year +
district** and normalize case/suffixes first.

## Winners (authoritative from this file) & the "Hales" cross-check

- **Mayor:** **BRETT A. HALES** won **2021** (6 108 vs Clark Bullen 4 369) and **2025**
  (6 490 vs Bruce E. Turner 4 005; also won the 2025 primary). No 2023 mayor race (B cycle).
- **Councilmember "Hales" vs Mayor Brett Hales — SAME PERSON.** The election record shows
  **Brett A. Hales** won **Murray City Council District 5** in **2011** and **2015**
  (general) — *below the 2020 floor, so those rows are not in these CSVs* — then moved up to
  **Mayor** in 2021 and 2025. There is **no separate sitting councilmember named Hales**;
  the roster's "Councilmember Hales" and "Mayor Brett Hales" are one individual who
  transitioned from the D5 council seat to the mayoralty. (Clark Bullen is the recurring
  foil — lost mayor to Hales in 2021, lost D3 in 2023, and finally won the **2025 D3 2-year
  special**.)
- In-scope district winners: **2021** D2 Pamela J. Cotter, D4 Diane Turner · **2023** D1
  Paul Pickett, D3 Rosalba Dominguez, D5 Adam Hock · **2025** D2 Pamela Jane Cotter,
  D4 Diane Turner (uncontested), D3-special Clark Bullen.

## Gaps / caveats

- **Below the 2020 floor:** the 2007–2017 Murray cycles exist in the county long file but
  remain out of scope. **The 2019 general (D1/D3/D5) + 2019 primary (D1/D3) ARE NOW INCLUDED**
  (hand-appended 2026-07-17 from the SOVC re-parse — see dated note). The Hales D5 council
  wins (2011/2015) still live only in the county file, not here.
- **2021 primaries (corrected 2026-07-17; CERTIFIED + cause-corrected 2026-08-01 — see the
  dated section at the end):** the **2021 MAYOR primary WAS held** (4 candidates —
  Hales 4,952 / Bullen 2,483 / Fitzgerald 413 / Teemsma 356) and is now certified by Murray's
  own **Board of Canvassers' Report** (retained in `raw/`). The **2021 D4 primary was NOT held
  or canvassed** — three candidates had declared, but Skylar L. Galt left the race before
  election day and Turner + Rasmussen advanced straight to the general. The earlier
  "**withdrew pre-certification**" wording was an **unsourced inference and is WRONG on timing**
  — both D4 candidates had already filed 2021-08-03 **Pre-Primary** disclosures, a slot Murray
  marks "Disclosure not required" when a race has no primary, so the D4 primary was still live
  a week out. No 2021 D2 primary (≤2 candidates). Likewise **no 2023 D5 primary** and
  **no 2025 D4 primary** (D4 2025 drew a single candidate → uncontested general, Diane Turner;
  the 2025 canvass confirms it by declaring Turner nominated with no primary contest). This
  closes the campaign-finance "2021 primary (Mayor ×4, D4 ×3)" review lead.
- **2021 method-level suppression** is fully resolved via the raw-workbook `Total` rows
  (above); if the county repo ever re-normalizes 2021 without suppression, the long-file
  path can replace the xlsx parse (delete the `SKIP` entry).
- `total_first_choice_votes` is blank everywhere — Murray did **not** join the 2021 RCV
  pilot; all races are plurality, vote-for-1.


## 2026-07-17 — SOVC-reparse rows appended (owner-approved, hand-edited)
Six rows were **hand-appended** to `murray_races.csv` from the 2026-07-16 SLCo raw-SOVC
re-parse (landed in `salt_lake_county/elections/`), the ONE sanctioned way audited election
files are edited (kearns precedent; dated backup in
`_backups/2026-07-17-audited-election-rows/murray/`):
- **2019 general** D1 (Kat Martinez d. Jake Pehrson 990-853), D3 (Rosalba Dominguez d. Adam
  Thompson 1050-883), D5 (Brett A. Hales UNOPPOSED 1445) — source `2019-11-05-general-election-sovc.xlsx`.
- **2019 primary** D1 (Martinez 647 / Pehrson 500 / Nicponski 321), D3 (Dominguez 565 /
  Thompson 449 / Brass 439) — source `2019-08-13-municipal-primary-sovc.xlsx`.
- **2021 MAYOR primary** (Hales 4,952 / Bullen 2,483 / Fitzgerald 413 / Teemsma 356) —
  **contest-grain** from the election-night report `2021-08-10-primary-election-results.pdf`
  (no precinct SOVC workbook exists for the 2021 primary); `registered_voters`/`ballots_cast`/
  `turnout_pct` are blank for that row by necessity.
  **SUPERSEDED 2026-08-01** (see the section below): the row's `source_file` is now the city's
  certified canvass `2021-08-24-murray-primary-canvass-report_docid12340.pdf` (the ENR PDF's
  four tallies were confirmed identical by it and remain cited in the row `note`), and the
  three fields called "blank by necessity" are now populated from that canvass —
  **28,531 / 8,244 / 28.89**. The necessity was real only against the county source.
- The 2019 district rows carry `registered_voters` (summed from the SOVC precinct rows,
  reproduces the sibling recovered-row method) but blank `ballots_cast`/`turnout_pct` (the
  method-split SOVC prints no clean contest total). All tallies re-verified twice vs the county
  layer. `clean_elections.py` will NOT regenerate these rows — re-append after any rebuild.

## 2026-08-01 — 2021 Mayor/D4 primary discrepancy flags CLOSED (certified city canvass)

The campaign-finance layer's two open **DISCREPANCY FLAGS** (`../campaign_finance/AVAILABILITY.md`
§"DISCREPANCY FLAGS", carried forward as unresolved since 2026-07-13) were worked to a **city
primary source** and are now closed. `raw/` is created by this pass — the **first and only**
local raw mirror in this dataset (the county SOVC remains un-mirrored by design; this is a
**city-published** document the county layer does not carry):

    raw/2021-08-24-murray-primary-canvass-report_docid12340.pdf   (+ .txt sidecar)
    sha256 748f0bd66bf036b523f09fe6c444ea98c371f6e138042a0e8179e0aec876906d
    Murray City DocumentCenter/View/12340 ("2021-Primary-Canvass-Notice"), retrieved 2026-08-01

**What the canvass certifies** (signed 2021-08-24 by Mayor D. Blair Camp, all five
councilmembers, and Recorder Brooke Smith): the August 10, 2021 Murray City Municipal Primary
Election was held **"for the offices of City Mayor"** — that office **alone**. Hales 4,952 /
Bullen 2,483 / Fitzgerald 413 / Teemsma 356, total 8,204; Hales + Bullen declared nominated.

**Finding 1 — the Mayor primary row is CORRECT and is now UPGRADED, not corrected.** All four
tallies, the total, the winner, the runner-up and both margins already matched the county
election-night PDF exactly (0 discrepancies). The canvass adds the three fields the row had
honestly left blank: **`registered_voters=28531`, `ballots_cast=8244`, `turnout_pct=28.89`**
(the ENR PDF prints county-wide voting data only, so those were genuinely unavailable before).
`ballots_cast` (8,244) exceeds `total_votes` (8,204) by **40 undervotes** — expected, not an
error. `source_file` now cites the canvass; the ENR PDF is retained as the corroborating
second source in the row `note`.

**Finding 2 — no 2021 D4 primary exists to be missing.** The contest appears in **neither**
the city canvass **nor** the countywide ENR contest list (which carries just 6 contests across
5 cities — Herriman Mayor, Murray Mayor, Taylorsville D5, West Jordan At-Large, West Valley
Mayor, West Valley D2 — corroborated by contemporaneous reporting of "five Salt Lake County
cities" holding primaries). The county's normalized long file likewise carries **zero** 2021
municipal-primary Murray rows. `murray_races.csv` carrying no 2021 D4 primary race is
therefore **correct**, and CF flag #1's D4 half is **premise-failed**.

**Finding 3 — the previously-filed CAUSE was wrong, and the CF evidence is why.** The
2026-07-17 note asserted Galt "withdrew pre-certification." Murray's own filing record
contradicts that timing: **both** eventual D4 general candidates (Rasmussen, Turner) filed
**Pre-Primary** statements on **2021-08-03**, one week before the primary. That slot is not
pro-forma — Murray posts "Disclosure not required" for it whenever a race has no primary, and
the pattern holds across every cycle in the CF index (2021 D2: none · 2023 D5: none · 2025 D4:
none · every race that DID have a primary: filed). So the D4 primary was still live at the
pre-primary deadline and collapsed **after** it. Galt filed **nothing at all** — no
pre-primary, and none of the "Post-Primary final (eliminated in primary)" statements the two
losing mayoral candidates filed — i.e. he was never a primary loser. Secondary reporting
(Murray Journal, 2021-11-23) says he "dropped out days before the primary." **The mechanism is
NOT documented in any acquired primary source and is not asserted as fact** anywhere in this
dataset; the row note states only what the canvass proves plus the sourced, labelled secondary
account.

**Finding 4 — CF flag #2 (Galt absent from `election_results`) is premise-failed.** Galt
appeared on no counted ballot in any Murray contest — no primary was conducted in D4 and he
was not on the general ballot (2021 D4 general: Turner + Rasmussen, `n_candidates=2`). His
absence from the election layer is **correct**, not a gap; his zero filings are consistent
with a candidacy that ended before any post-primary obligation attached.

**Known, unchanged asymmetry (not a defect):** the six hand-appended races (2019 ×5 + this
2021 Mayor primary) have rows in `murray_races.csv` **only** — no `murray_results_by_candidate.csv`
/ `murray_results_by_precinct.csv` rows, because no precinct SOVC exists for the 2021 primary
and the 2019 appends were contest-grain. A races→by_candidate join drops those 6 of 21 races;
that is a documented provenance boundary, not a missing extraction.
