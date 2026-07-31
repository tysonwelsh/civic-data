# election_results — Midvale City municipal elections

Midvale City (**Salt Lake County**, Utah) municipal **general + primary** election results,
normalized to the SLC/Sandy/South-Jordan sibling schema. Three CSVs + a reproducible build
script (`clean_elections.py`) + the retained raw county source files under `raw/`.
**Do not edit the CSVs by hand — regenerate** (see "Rebuilding"). Built 2026-07-11.

## Council / mayor structure

Midvale is a Utah **six-member-council** city: a **5-member council elected by DISTRICT
(Districts 1–5)** plus a **separately elected Mayor** (citywide). 4-year staggered terms,
odd-year municipal elections, so each cycle fills only part of the body:

| Cycle | Seats up | Years |
|---|---|---|
| **A** | **Mayor + District 4 + District 5** | 2009, 2013, 2017, 2021, 2025 |
| **B** | **Districts 1, 2, 3** | 2007, 2011, 2015, **2019**, 2023 |

The Mayor is elected only on the **A** cycle. (The Mayor votes only on ties / mayoral-power
ordinances / city-manager hire-fire — a vote-extraction nuance, not an elections one.)

## Ranked Choice Voting (2021, 2023, 2025) — READ THIS BEFORE QUOTING MARGINS

Midvale joined the Utah / Salt Lake County **RCV municipal pilot in 2021, 2023 and 2025**
(externally confirmed — SL Tribune, Midvale Journal, `rcvis.com`; the city's own
`.../elections/ranked_choice_voting.php`). The county SOVC **`Total` column carries
FIRST-CHOICE (round-1) tallies, not the RCV final round.** Therefore for those three years:

- `voting_method = 'ranked choice'` (all other years `plurality`); `total_first_choice_votes`
  is populated (= `total_votes`, i.e. the first-choice sum).
- **Winners are authoritative** — each RCV-final winner here also led the first choice, so the
  `winner` column is correct in every race. Verified externally: **2021 Mayor** Marcus
  Stevenson (def. incumbent Robert Hale), **2023 D3** Heidi Robinson (def. Evan Feinberg in the
  RCV runoff), **2025 Mayor** Dustin Gettel (61% first-place, majority).
- Two races had **no round-1 majority**, so the RCV redistribution (not in the SOVC) set the
  final spread — these carry a **`note`** flag: **2021 Mayor** (Stevenson 45.72% first-choice)
  and **2023 D3** (Robinson 38.97% first-choice). In those rows `winner_pct`/`margin_*` are
  **first-choice only**; do not quote them as final margins. All other RCV races had a round-1
  majority (or ≤2 candidates), so their pct/margin equal the final result.

This mirrors the collection's **millcreek** RCV convention (take winners from the canvass; the
per-precinct/round-1 order is not the RCV final).

## Source

**Salt Lake County Clerk** SOVC (Statement of Votes Cast). The **primary source is the county
canonical long-form file**
`/Users/tysonwelsh/civic-data/salt_lake_county/elections/slco_municipal_results_long.csv`
(filtered to Midvale — `contest` contains `MIDVALE`, the **BOND question excluded**). The build
writes that filter to `raw/municipal_results_long_midvale.csv` (retained provenance, 3,256 rows
after de-duping 26 all-zero phantom rows). Rows are precinct- **and vote-method-level** with no
explicit "Total" method row, so **precinct totals are recovered by summing across the method
rows** (2025 already arrives pre-summed as method `ALL`). Consumed straight for
2007/2009/2011/2013/2015/2017 (+ primaries), 2023, 2025.

Two contests are **re-parsed directly from the raw county spreadsheets** (`raw/sovc/*.xlsx`)
because the long file does not deliver them cleanly:

| Contest | Problem | Recovery |
|---|---|---|
| **2019 general** (D1/D2/D3) | **Absent** from the long file — the county normalizer keyed the contest off the sheet name and the 2019 sheets are coded **`MID Council N`**, so a `%MIDVALE%` filter never matched. **This is the `recon.md` 2019 gap.** | Re-parsed `2019-11-05-general-election-sovc.xlsx` (`MID Council 1/2/3`, Family-A wide crosstab). |
| **2019 primary** (D2 only) | Same — 2019 primary sheets are numbered; Midvale's single primary (D2, 3 cands) sits on sheet `11`. | Re-parsed `2019-08-13-municipal-primary-sovc.xlsx`. (D1/D3 drew ≤2 candidates → no primary. Verified.) |
| **2021 general** (Mayor/D4/D5) | Present but the In-Person/Vote-By-Mail method split is **privacy-suppressed** (`****`, blank votes) — destroys every precinct's usable count. | Re-parsed `2021-11-02-general-election-sovc.xlsx` (Sheets 19/20/21), whose per-precinct **`Total`** sub-rows are un-suppressed. |

After recovery the final CSVs have **zero suppressed cells** and every by-precinct sum
reconciles exactly to its by-candidate total (build asserts 0 mismatches).

## The three CSVs

- **`midvale_races.csv`** — one row per race (**39: 30 general + 9 primary**). The **25-column**
  superset schema (header identical to `south_jordan_races.csv`): `office`/`district`/`contest`
  (canonical) + `contest_verbatim`, `n_candidates`, `voting_method`, `total_votes`,
  `total_first_choice_votes` (RCV years only), `winner`/`winner_votes`/`winner_pct`,
  `runner_up`/`runner_up_votes`, `margin_votes`/`margin_pct`,
  `registered_voters`/`ballots_cast`/`turnout_pct` (populated where the source carries them —
  2021/2023/2025 + some earlier years; blank otherwise), `uncontested`,
  `suppressed_precincts` (`False` everywhere in the final data), `note`, `source_file`.
- **`midvale_results_by_candidate.csv`** — race × candidate (**102 rows**): `votes`, `pct`,
  `rank`, `is_winner`.
- **`midvale_results_by_precinct.csv`** — precinct × candidate (**991 rows**). Precinct IDs are
  `MID###` (2019+) and older county numeric IDs (`4502`, `4516C`) for 2007–2017. No suppressed
  cells survive.

## The 2023 BOND question — deliberately EXCLUDED

The long file also carries **`MIDVALE CITY REVISED RESOLUTION CALLING BOND ELECTION NO.
2023-R-32`** (a ballot question, not a seat): **FOR 2,345 / AGAINST 1,499** (bond passed). It is
**not a candidate race** and is **excluded** from all three CSVs (`is_midvale_seat()` drops any
label containing `BOND`). Recorded here so the omission is intentional, not a gap.

## Name normalization

`norm_name()` normalizes each candidate name **alongside** the verbatim source (never
overwrites): collapses whitespace, strips the `(NP)` / `(NON)` non-partisan tag (incl. the
`(NP )` inner-space county variant), drops the leading `*` write-in mark, canonicalizes
write-ins to `Write-in` / `Write-in (unresolved)`. To join elections ↔ `all_votes.csv`, further
strip case (election names are UPPER-CASE; minutes names are mixed-case).

## Verification / cross-checks (2026-07-11)

**All six current officeholders reproduce from the winners** and match `recon.md` / the city
council page: Mayor **Dustin Gettel** (won 2025; appointed 2024 after Marcus Stevenson resigned;
previously D5 2017 & 2021), D1 **Bonnie Billings** (2023), D2 **Paul Glover** (2007/2011/2015/
2019/2023 — long tenure), D3 **Heidi Robinson** (2019/2023), D4 **Bryant Brown** (2017/2021/
2025), D5 **Denece Mikolash** (2025, open seat after Gettel moved to Mayor).

External cross-checks: **2021 Mayor** Stevenson def. incumbent Hale — confirmed (SL Tribune /
Midvale Journal; RCV). **2025 Mayor** Gettel 61% first-place, Boyer ~20%, Fair ~19% — matches the
CSV (Gettel 3192 / 60.89%). **2023 D1** Billings won (news reported election-night 547; the CSV's
641 is the higher **final canvass** — winner unchanged). **2023 D3** Robinson def. Feinberg in the
RCV runoff — confirmed. Notable close first-choice races: **2021 Mayor** Stevenson +99 (first-
choice), **2013 D5 primary** Brown +3, **2017 D4 primary** Brown +10.

## Rebuilding

```
cd election_results && python3 clean_elections.py            # writes the slice + 3 CSVs
                       python3 clean_elections.py --report    # + per-race summary
```
Idempotent. Re-run when a new cycle posts to the county: it re-reads the county canonical file
(and, for any new suppressed/gap year, add a raw parser call mirroring 2019/2021). Mind whether
the cycle is A (Mayor+D4+D5) or B (D1/D2/D3) and whether Midvale used RCV that year.

## Gaps / caveats

- **No 2019 primary** for D1/D3 (≤2 candidates each — a true no-contest, not a gap); only D2 had
  a 2019 primary.
- **Turnout** is populated only where the source carries registered-voter / ballots-cast counts
  (reliably 2021/2023/2025; sporadic earlier). Older method-split years leave `turnout_pct` blank
  or approximate.
- **RCV years (2021/2023/2025):** see the RCV section — margins in the two flagged rows are
  first-choice, not final.
- **Vote-for-1 everywhere** — single-member districts + citywide Mayor; no at-large / vote-for-N.
- Precinct geometry for joins: `../geo/` (Midvale's own council-district layer is the preferred
  geo source; `precinct_to_district.csv` maps `MID###` → district).
