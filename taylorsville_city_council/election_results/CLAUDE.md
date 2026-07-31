# election_results — Taylorsville City municipal elections

Taylorsville City (**Salt Lake County**, Utah) municipal **general + primary** election
results, normalized to the SLC/Sandy/South Jordan sibling schema. Three CSVs + a
reproducible build script (`clean_elections.py`) + the retained raw county source files
under `raw/`. **Do not edit the CSVs by hand — regenerate** (see "Rebuilding").

## Council / mayor structure

Taylorsville is a **Council–Mayor (executive-mayor) city**: a **5-member council elected by
DISTRICT (Districts 1–5)** plus a **separately elected Mayor** (citywide, executive — the
Mayor does not sit on / vote in council). 4-year staggered, non-partisan terms, so each
odd-year cycle fills only part of the body:

| Cycle | Seats up | Years |
|---|---|---|
| **A** | **Mayor + District 4 + District 5** | 2009, 2013, 2017, 2021, 2025 |
| **B** | **Districts 1, 2, 3** | 2007, 2011, 2015, 2019, 2023 |

The Mayor is elected only on the **A** cycle. Contest labels drift year to year
(`TAYLORSVILLE CITY COUNCIL 1`, `TAYLORSVILLE COUNCIL DISTRICT 4`, `Taylorsville City Coun
2`, `TAYLORSVILLE CITY CNCL DIST 4`, `CITY OF TAYLORSVILLE COUNCIL DISTRICT 3`, …); all
normalize to `Taylorsville City Council District N` / `Taylorsville City Mayor`
(preserved verbatim in `contest_verbatim`). The **Taylorsville-Bennion Improvement
District** contests (a separate special district, not the city council/mayor) are
excluded.

### Two out-of-cycle District 3 special / unexpired-term elections (flagged in `note`)

District 3's regular cycle is **B** (2007/2011/2015/2019/2023), so a D3 contest in a
Cycle-A year is a special election filling an unexpired term. There are **two**:

- **2013 D3** — the 2011 D3 winner **Jerry Rechtenbach** ran for **Mayor** in 2013 (he is
  the 2013 Mayor runner-up), vacating D3. **Brad Christopherson** won the 2013 balance
  (uncontested), then the full D3 term in 2015.
- **2021 D3** — the 2019 D3 winner (**Christopherson**) vacated; **Anna Barbieri** won the
  2021 balance (uncontested), then the full D3 term in 2023.

Both carry an explanatory string in the `note` column of `taylorsville_races.csv`. Neither
is a permanent cycle shift — treat member-term logic accordingly. (The recon flagged only
the 2021 special; the 2013 one was surfaced from the data during the build.)

## Source

All results are **Salt Lake County Clerk** SOVC (Statement of Votes Cast) data. Two
provenance layers:

1. **The county canonical long file** — `salt_lake_county/elections/slco_municipal_results_long.csv`
   (the county-clerk SOVC held once at the level where it originates; built by the archive's
   `scripts/normalize_sovc.py` from the raw spreadsheets). `clean_elections.py` reads it
   **directly** and filters to Taylorsville council/mayor contests. Precinct- and
   vote-method-level. Consumed for **2007, 2009, 2011, 2013, 2015, 2017** (+ their primaries),
   the **2019 municipal primary (District 1)**, and the **2023 & 2025** generals — all with
   **zero suppression**, summing cleanly to contest totals. **(Re-point 2026-07-19:** the old
   redundant per-city copy `raw/municipal_results_long_taylorsville.csv` was retired after
   verifying the re-pointed build reproduces all three CSVs **byte-identically** (sole diff =
   the newly-adopted 2019 D1 primary); the `precinct='Cumulative'` workbook-rollup rows the
   county canonical now labels are excluded — never a precinct; the **2019 general** the
   canonical carries only under the sheet code `TAY Council N` is skipped in the long-file read
   because the raw parser below recovers it with faithful district numbers + the in-cell label.)
2. **`raw/sovc/*.xlsx`** — the true county SOVC spreadsheets, re-parsed directly by the
   build for the **two contests the long file does not deliver cleanly** (see below).

## The two gaps recovered from raw

| Contest | Why the archive parse missed / broke it | Recovery |
|---|---|---|
| **2019 general** (Dist 1/2/3) | Present in the county canonical only under the raw **sheet code `TAY Council N`** (the normalizer keyed the contest name off the sheet name, which lacks the `TAYLORSVILLE` string, so a `%TAYLORSVILLE%` contest filter never matches it). **This is the gap flagged in `recon.md`.** | Re-parsed `raw/sovc/2019-11-05-general-election-sovc.xlsx` (`TAY Council N` sheets; Family-A wide crosstab; the in-cell label IS `TAYLORSVILLE CITY COUNCIL DISTRICT N`) for faithful district numbers, candidate names, precinct totals. |
| **2021 general** (Mayor/D3/D4/D5) | Present but **106/158 rows privacy-suppressed** (`****`) at the In-Person/Vote-By-Mail method split, destroying precinct totals. | Re-parsed `raw/sovc/2021-11-02-general-election-sovc.xlsx`, whose per-precinct **`Total`** sub-rows are **not** suppressed. |

After recovery the final CSVs have **zero suppressed cells** and **every by-precinct sum
reconciles exactly to its by-candidate total** (the build asserts 0 mismatches).

**2019 municipal PRIMARY (District 1) — a primary WAS held (adopted 2026-07-19).** District
1 drew **3 candidates** (Burgess / Gehrke / Quigley), which triggered a primary. The county
canonical carries it on sheet `25` of `2019-08-13-municipal-primary-sovc.xlsx`
(`TAYLORSVILLE CITY COUNCIL DISTRICT 1`): **Burgess 728 / Gehrke 371 / Quigley 229**
(total 1,328), **cell-verified against the raw workbook's own `Total:` row** and its 5
per-precinct sub-rows (TAY001/002/004/007/008), zero suppression, no method-label
pseudo-candidates. The primary's **top-2 (Burgess, Gehrke) are exactly the two candidates
in the 2019 D1 general** — an internal cross-corroboration. Adopted into the audited layer
directly from the county canonical (the earlier `no 2019 primary` claim — from the
now-retired per-city archive slice that had dropped the whole 2019 Taylorsville set — was
**incorrect** and is corrected here). The **other** Cycle-B districts drew no primary (D2 =
2 candidates, D3 = 1), and 2007/2009/2015/2023/2025 likewise drew ≤2 per seat → no primary
those cycles. Logged, not fabricated.

## The three CSVs

- **`taylorsville_races.csv`** — one row per race (**39 races: 32 general + 7 primary**).
  Same columns as the South Jordan sibling **plus a `note` column** (used only for the two
  D3 specials): `office`/`district`/`contest` (canonical) + `contest_verbatim`,
  `n_candidates`, `total_votes`, `winner`/`winner_votes`/`winner_pct`,
  `runner_up`/`runner_up_votes`, `margin_votes`/`margin_pct`,
  `registered_voters`/`ballots_cast`/`turnout_pct` (populated where the source carries them
  — the 2019 raw + 2021/2023/2025 provide reg/ballots; older archive years often don't →
  blank), `uncontested`, `suppressed_precincts` (`False` everywhere in the final data),
  `note`, `source_file`.
- **`taylorsville_results_by_candidate.csv`** — race × candidate (**93 rows**): `votes`,
  `pct`, `rank`, `is_winner`.
- **`taylorsville_results_by_precinct.csv`** — precinct × candidate (**1,368 rows**).
  Precinct IDs are `TAY###` for 2019→2025; older county-wide numeric IDs for 2007–2017.
  `suppressed=True` marks a redacted county cell (**none survive** in the final data).

## Name normalization

`norm_name()` normalizes each candidate name **alongside** the verbatim source value (never
overwrites raw): collapses whitespace, strips the `(NP)` / `(NON)` non-partisan tag, drops
the leading `*` registered-write-in mark, and canonicalizes write-ins to `Write-in` /
`Write-in (unresolved)`. Note **2013 D3/D4 were genuine write-in contests** (D4: Barbour
635 def. aggregate `Write-in` 295 and registered write-in `Wendi Wengel` 150) — faithful,
not a defect. To join elections ↔ votes, further strip case/suffixes as the playbook
describes (council `all_votes.csv` names are mixed-case).

## Verification / cross-checks

- **All six current officeholders (per `recon.md`) confirmed in the data**: Mayor
  **Kristie Steadman Overson** (won 2017, 2021, 2025 — and earlier served as **District 2**
  council member, winning 2011 & 2015 before moving up to Mayor); **D1 Ernest ("Ernie")
  Glen Burgess** (2011/2015/2019/2023); **D2 Curt Cochran** (2019/2023); **D3 Anna
  Barbieri** (2021 special + 2023 full term); **D4 Meredith Harker** (2017/2021/2025);
  **D5 Bob Knudsen** (2021/2025).
- **2017 Mayor (external):** Councilwoman Overson unseated incumbent Mayor Larry Johnson
  with ~57% — matches the CSV exactly (Overson 5444 / **57.2%** vs Johnson 4073).
  (Taylorsville Journal, 2017-12-01.)
- **2021 D5 (external):** Bob Knudsen defeated former Mayor Larry Johnson for the open D5
  seat — matches the CSV (Knudsen 914 vs Johnson 825, margin **89**). (Taylorsville
  Journal.)
- Notable close races: **2011 D1** Burgess +70 (and its primary +17 over Grossman), **2021
  D5** Knudsen +89, **2013 D5** Armstrong +103 (after *losing* the primary to Acker).

## Rebuilding

```
cd election_results && python3 clean_elections.py            # reads the county canonical, writes the 3 CSVs
                       python3 clean_elections.py --report    # + per-race summary
```
Idempotent; prints the precinct-sum reconciliation mismatch count (must be 0). Re-run only
when a **new cycle** posts to the county site: add its SOVC to the county archive so
`salt_lake_county/elections/slco_municipal_results_long.csv` picks it up, then either (a)
rely on the direct long-file read if the canonical covers the new year cleanly, or (b) add
its raw SOVC to `raw/sovc/` + a raw parser call in `clean_elections.py` (mirror the
2019/2021 handling) for any contest the long file suppresses or mislabels. Mind whether the
cycle is A (Mayor+D4+D5) or B (D1/D2/D3), and watch for another out-of-cycle D3/D-special.

## Gaps / caveats

- **A 2019 primary WAS held (District 1 only)** — adopted 2026-07-19 (see the Source /
  "2019 municipal PRIMARY" note above). No **2007/2009/2015/2023/2025** primary — those
  cycles drew ≤2 candidates per seat (true no-contests, not data gaps).
- Turnout is populated only where the source carries registered-voter / ballots-cast
  counts (2019 raw, 2021, 2023, 2025); older archive-slice years leave `turnout_pct` blank.
- **Vote-for-1 everywhere** — each council seat is a single-member district, so there are
  no at-large / vote-for-N races and no RCV (Taylorsville was **not** in the 2021 municipal
  RCV pilot; 2021 was plurality).
- Precinct geometry for joins: `~/Desktop/slco-election-archive/geo/` (join `PrecinctID`);
  the city has no published council-district GIS layer (see `../geo/` — districts derive
  from precinct→district assignment; boundaries were redistricted after the 2020 census, so
  pre-2022 vs 2022+ precinct sets differ).
