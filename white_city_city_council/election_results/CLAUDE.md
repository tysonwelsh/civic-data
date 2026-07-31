# election_results — White City municipal elections

White City (**Salt Lake County**, Utah) municipal **general** election results, normalized
to the SLC / South-Jordan sibling 25-column schema. Three CSVs + a reproducible build
(`clean_elections.py`) + retained raw county sources under `raw/`. **Do not edit the CSVs
by hand — regenerate.** Data floor: **2017** (metro township seated Jan 2017). As-of build:
**2026-07-12**.

## White City structure (important for interpretation)

White City's governing body has been **5 voting people the entire time**, but the entity
FORM and the ballot changed mid-record (HB35, 2024):

- **Metro Township era (2017 → Apr 2024):** a **5-member, all-at-large council**; the
  council picks one member as **Chair**, who carries the courtesy title "Mayor" and
  **votes as a member** (Paulina Flint, 2021–2025). No separately-elected executive mayor.
- **City era (from 2024-05-01, HB35):** **mayor–council** form — a **directly-elected
  executive Mayor + 4 at-large council seats (A–D)**; the Mayor **votes** on every roll
  call. First directly-elected mayor: **Allan Perry (2025)**.

**No council districts, ever — all seats are AT-LARGE.** An address→representative question
is therefore citywide (see `../geo/`), not by district.

## Election cycles actually on the ballot (what exists)

| Year | Contest(s) | Seats | Winner(s) |
|---|---|---|---|
| **2016** (even-yr) | initial 5-member metro-township council | 5 | *NOT in this dataset* — see gap note |
| **2019** | White City Metro Township Council At-Large | 3 | **Little, Perry, Flint** (Cutler lost) |
| **2023** | White City Metro Township Council At-Large | 3 | **Flint, Shelton, Huish** (Van Horn, West lost) |
| **2025** | Mayor + Council At-Large B + Council At-Large C | 1+1+1 | **Perry** (mayor), **Price** (B), **Mahoney** (C) |

**5 race rows total** (1×2019, 1×2023, 3×2025); years **[2019, 2023, 2025]**.

## Source & the one recovered contest

Salt Lake County Clerk **SOVC** (Statement of Votes Cast), two provenance layers in `raw/`:

1. **`raw/slco_municipal_results_white_city.csv`** — the archive-normalized SOVC
   (`salt_lake_county/elections/slco_municipal_results_long.csv`) filtered to every
   `WHITE CITY` contest (446 long rows: candidate × precinct × vote-method). Delivers the
   **2023 + 2025** council/mayor contests cleanly (precincts **WHT001–WHT004**, zero
   suppression, precinct sums reconcile exactly to contest totals).
2. **`raw/2019-11-05-general-election-sovc.xlsx`** — the true county spreadsheet,
   re-parsed directly (sheet **`WHT At-Large`**) for the **one contest the archive
   normalizer dropped**: the **2019 general Metro Township Council At-Large**. Same
   failure mode South Jordan hit in 2019 — the normalizer keyed metro-township contests
   off a sheet code, so a `%WHITE CITY%` filter never matched. Recovered 4 candidates /
   4 precincts; the three winners (Little/Perry/Flint) all subsequently served.

## Decoys EXCLUDED (verified — never council races)

- **`WHITE CITY WATER`** (2013) — the **White City Water Improvement District** board
  (Garry True, Dortha Robinson, et al.). A *separate* special district; the township/city
  merely rents the water district's building (999 E Galena) as its meeting venue.
- **`WHITE CITY MSD`** (2015) — Municipal Services District **ballot question** (YES 961 /
  NO 142), not a candidate race.
- **`WHITE CITY METRO TOWNSHIP-CITY`** (2015) — incorporation **ballot question**
  (Metro-Township option 914 vs 183), not a candidate race.

## The election gap — resolved, not fabricated

`recon.md` flagged a "**2017 / 2019 / 2021** gap." Investigation resolves it:

- **2019 — RECOVERED** (see above). The only true parse-drop.
- **2017 — genuine no-election.** The initial 5-member metro-township council was elected
  in the **Nov-2016 even-year general** (incorporated Jan 1 2017), so White City is
  off-cycle in 2017. The 2017 SOVC carries the peer small townships **Copperton** and
  **Emigration** at-large races but **no White City contest** — a real absence, not a
  scraper miss. (The 2016 general is an even-year county race outside this odd-year
  municipal archive; not ingested.)
- **2021 — genuine absence in the SOVC.** The 2021 SOVC carries Copperton/Kearns/Magna
  metro-township council races but **no White City contest**. The seats later labelled
  **B (Price) / C (Cardenaz)** appear to have been filled **uncontested in 2021**, and
  uncontested SLCo seats routinely carry no SOVC tally sheet → no tally to ingest. Logged
  as an honest gap; **not** fabricated.

## The three CSVs

- **`white_city_races.csv`** — one row per race (**5 races**), the 25-col sibling schema.
  `district` = `At-Large` (2019/2023 multi-seat), `At-Large B` / `At-Large C` (2025 single
  seats), blank for the citywide **Mayor**. `voting_method=plurality` (no RCV). `n_seats`
  is the vote-for. `registered_voters` populated from the SOVC; `ballots_cast`/`turnout_pct`
  left blank (SOVC gives per-candidate totals, not a clean ballot count for the multi-seat
  at-large rows).
- **`white_city_results_by_candidate.csv`** — race × candidate (**18 rows**): `votes`,
  `pct`, `rank`, `is_winner` (top-`n_seats` real candidates).
- **`white_city_results_by_precinct.csv`** — precinct × candidate (**72 rows**), precincts
  **WHT001–WHT004**, `suppressed=False` throughout.

## At-large multi-seat convention (matches West Jordan / Sandy / West Valley)

For a multi-seat at-large race: `winner` = top vote-getter; `runner_up` = the **first
loser** (the `n_seats+1`-th candidate); `margin_votes` = `winner_votes − first_loser_votes`
(top winner vs top loser). `is_winner` marks the top `n_seats` real candidates.

## Name normalization

`norm_name()` normalizes alongside (never over) the verbatim county value: collapses
whitespace, strips `(NP)`, drops leading `*` (registered write-in) and the trailing
`Qualified Write In` tag (keeping the person's name), and canonicalizes unresolved write-ins
to `Write-in (unresolved)`. To join elections ↔ council votes, further strip case/suffixes
(council `all_votes.csv` names are mixed-case; election names are UPPER-CASE).

## Verification / external cross-check (2026-07-12)

- **2025 Mayor** (Salt Lake Tribune + `whitecity.utah.gov`): **Allan Perry def. Paulina
  Flint 61.9% / 38.1%** — matches the CSV exactly (Perry 740 / Flint 456).
- **2025 council** (`whitecity.utah.gov/elections`): **Linda Price** (Seat B) and **Neil
  Mahoney** (Seat C) elected — matches (Price 730 > write-in Denning 307; Mahoney 635 >
  incumbent Cardenaz 536).
- **2019 winners** (Little/Perry/Flint) confirmed by service history: Perry a 2021
  councilmember, Flint 2021–2025 Chair/"Mayor," Scott Little served until his death Nov 2022
  — all three seated, corroborating the 3-seat recovery.

## Rebuilding

```
python3 clean_elections.py            # reads raw/, writes the 3 CSVs (idempotent)
python3 clean_elections.py --report   # + per-race summary
```
Re-run when a new odd-year cycle posts: add its SOVC to `~/Desktop/slco-election-archive`,
refresh `raw/slco_municipal_results_white_city.csv` from the county elections layer, and
(if the archive normalizer drops the metro-township/at-large sheets again) mirror the 2019
raw-parse call. The build asserts every by-precinct sum reconciles to its by-candidate total.

## Gaps / caveats

- **No 2017 / 2021 White City council contest** (see gap note) — genuine, documented.
- **No RCV** — White City ran plurality every cycle (unlike Sandy 2021 / Millcreek).
- `ballots_cast` / `turnout_pct` blank (multi-seat at-large SOVC gives candidate totals,
  not a single ballot count). `registered_voters` is populated (2847 / 2951 / 2942).
- Precinct geometry for joins: `../geo/precincts.geojson` (WHT001–004).
