# election_results — Herriman City municipal elections

Herriman City (**Salt Lake County**, Utah) municipal **general + primary** election results,
normalized to the SLC/South-Jordan sibling schema. Three CSVs + a reproducible build script
(`clean_elections.py`) + retained raw county sources under `raw/`. **Do not edit the CSVs by
hand — regenerate** (see "Rebuilding").

## Council / mayor structure — it CHANGED below the 2020 data floor

Herriman is a **Council–Mayor** city, but the council's electoral structure shifted:

| Era | Structure | Years present |
|---|---|---|
| **At-large** | 2 at-large council seats per cycle (top-2 elected) + Mayor | **2007** (2 seats), **2009** (2 seats + Mayor) |
| **Districts** | **4 single-member districts (1–4) + separately-elected Mayor** | **2011** (first numbered "Council N") → present |

Numbered "Council 1/2/4" contests first appear in **2011**; the record is fully
**District N + Mayor** by 2013. The **entire 2020+ modelled record is stable 4-district +
Mayor** — the at-large→district change is well below the floor and does not affect
member-level joins. The **Mayor presides but casts no ordinary roll-call vote** (max
council tally = 4).

**District cycle map** (4-yr staggered, non-partisan):

| Cycle | Seats up | Years |
|---|---|---|
| **A** | **Mayor + District 2 + District 3** | 2013, 2017, 2021, 2025 |
| **B** | **District 1 + District 4** | 2011, 2015, 2019, 2023 |

**2025 additionally carried a `District 4 (2 Year Term)` off-cycle SPECIAL** (Terrah
Anderson) to fill an **unexpired D4 seat** vacated mid-term (Steven Shields, elected D4 in
2023, left) — flagged in the `note` column so term logic does not misread it as a cycle
shift. There is no regular D4 contest in 2025.

## Sources (Salt Lake County Clerk SOVC — retained under `raw/`)

1. **`raw/municipal_results_long_herriman.csv`** — a slice of the repo-wide canonical SOVC
   normalization (`salt_lake_county/elections/slco_municipal_results_long.csv`) filtered to
   Herriman (`HERRIMAN%` + the 2019 sheet-code rows `HER Council %`). Precinct- and
   vote-method-level. **Consumed directly** (summing per-method rows to precinct+candidate
   totals) for **2007, 2009, 2013, 2015, 2017** (+ their primaries), the **2011 primary**,
   and the **2023 & 2025** generals (+ 2025 primary) — all zero-suppression, summing cleanly.
2. **`raw/sovc/*.xlsx`** — the true county SOVC spreadsheets, re-parsed by the build for the
   **three general contests the canonical layer does not deliver cleanly** (below).

## The three contests recovered from raw

| Contest | Why the canonical slice missed / broke it | Recovery |
|---|---|---|
| **2011 general** (Council 1/2/4) | **Absent** from the canonical slice — the archive normalizer skipped Herriman's 2011-general sheets (same failure as South Jordan). | Re-parsed `raw/sovc/2011-11-08-municipal-general-sovc.xlsx` (`Herriman City Council N` sheets; per-precinct `Total` Type rows). |
| **2019 general** (District 1 & 4) | **The recon's "2019 GAP" — data was on disk, mis-labelled, not missing.** Present in the slice only under sheet codes `HER Council 1`/`HER Council 4`, with the candidate name replaced by `"Total"`/method labels (the normalizer keyed off the sheet name **and** mangled the Family-A wide crosstab). | Re-parsed `raw/sovc/2019-11-05-general-election-sovc.xlsx` (`HER Council N` sheets) for faithful candidate names + precinct totals. |
| **2021 general** (Mayor/D2/D3) | Present but **100 cells privacy-SUPPRESSED** (`****`) at the In-Person/Vote-By-Mail method split, destroying precinct totals. | Re-parsed `raw/sovc/2021-11-02-general-election-sovc.xlsx` (Sheets 13/14/15), whose per-precinct **`Total`** sub-rows are **not** suppressed. |

After recovery the final CSVs have **zero suppressed cells** and **every by-precinct sum
reconciles exactly to its by-candidate total** (the build asserts 0 mismatches on all
unsuppressed races).

**2019 municipal PRIMARY:** the raw 2019 primary SOVC contains **no Herriman sheet** (D1
drew 1 candidate, D4 drew 2) → Herriman held **no 2019 primary**. Logged, not fabricated.

## The three CSVs (25-col superset schema)

- **`herriman_races.csv`** — one row per race (**38 races: 25 general + 13 primary**).
  25 columns (SJ superset): `office`/`district`/`contest` (canonical) + `contest_verbatim`,
  `n_seats`, `n_candidates`, `voting_method` (=`plurality`), `total_votes`,
  `total_first_choice_votes` (blank — no RCV cycle in Herriman), `winner`/`winner_votes`/
  `winner_pct`, `runner_up`/`runner_up_votes`, `margin_votes`/`margin_pct`,
  `registered_voters`/`ballots_cast`/`turnout_pct` (where the source carries them),
  `uncontested`, `suppressed_precincts` (`False` everywhere in the final data), `note`,
  `source_file`.
- **`herriman_results_by_candidate.csv`** — race × candidate (**119 rows**): `votes`, `pct`,
  `rank`, `is_winner` (`True` for `rank <= n_seats`).
- **`herriman_results_by_precinct.csv`** — precinct × candidate (**1,256 rows**). Precinct
  IDs are `HER###` (2011→2025) and older county IDs for 2007/2009. `suppressed=True` marks a
  redacted county cell (**none survive** in the final data).

### Multi-seat (at-large) convention

2007 & 2009 council were **at-large, 2 seats** (`n_seats=2`; the primary advanced the top 4,
the general elected the top 2). For these rows: `winner` = top vote-getter,
**`is_winner=True` for the top 2**, `runner_up` = the highest **non-winning** candidate, and
`margin_votes` = the **last-seat margin** (2nd-place winner − 1st loser). The `note` column
lists every elected winner. Single-member-district races use `n_seats=1` (`runner_up` =
2nd place, the standard SJ semantics).

## Name normalization

`norm_name()` normalizes each candidate name **alongside** the verbatim source (never
overwrites raw): collapses whitespace, strips the `(NP)` non-partisan tag, drops the leading
`*` write-in mark, canonicalizes write-ins to `Write-in`/`Write-in (unresolved)`. Source
spelling variants persist across years (e.g. `CORALEE WESSMAN-MOSE` (2011 primary) vs
`WESSMANMOSER` (2011 general raw) vs `WESSMAN-MOSER` (2013) — all the same person). To join
elections ↔ minutes votes, further strip case as the playbook describes (`all_votes.csv`
names are mixed-case).

## Verification / external cross-checks (2026-07-11)

Winners confirmed against outside sources:

- **2025 Mayor**: Lorin Palmer **6,884** def. Ty R. Brady **2,267** — **exact** match to
  county certified results (SL Trib / Herriman Journal / county SOVC).
- **2021 Mayor**: Lorin Palmer def. Clint Smith **4,291 (63.2%) / 2,498 (36.8%)** — matches
  news reports (Palmer ~62% early unofficial; 63.2% final canvass).
- **2025 D3**: Matt Basham def. Heather Garcia (**1,583 / 1,197**) — matches (a mid-count
  news snapshot showed Basham 1,558; the CSV carries the final canvass 1,583; Garcia 1,197
  exact).
- **2025 D4** = Terrah Anderson (1,431, uncontested) — confirmed as the **2-year special**
  filling a mid-term vacancy.
- **Current roster** (matches `recon.md` + `herriman.gov/city-council`): Mayor **Lorin
  Palmer** (2021, 2025), D1 **Jared Henderson** (2015, 2019-unopposed, 2023), D2 **Teddy
  Hodges** (2021, 2025), D3 **Matt Basham** (2025), D4 **Terrah Anderson** (2025 special).

Notable close races: **2017 D3** Ohrn +9, **2017 D2** Smith +23, **2013 D3** Tischner +32,
**2017-primary D3** Stromberg +1.

## Rebuilding

```
cd election_results && python3 clean_elections.py            # reads raw/, writes the 3 CSVs
                       python3 clean_elections.py --report    # + per-race summary + reconciliation
```
Idempotent. Re-run only when a **new cycle** posts to the county: refresh the canonical
`slco_municipal_results_long.csv` slice (`raw/municipal_results_long_herriman.csv`), and if
the new year's split is suppressed or the normalizer mangles it, add its raw SOVC to
`raw/sovc/` + a parser call (mirror the 2011/2019/2021 handlers). Mind the cycle (A =
Mayor+D2+D3, B = D1+D4).

## Gaps / caveats

- **No 2019 primary** (a true no-contest, not a data gap).
- The recon's "2019 is a KNOWN GAP" is **resolved** — 2019 D1 & D4 were recovered from raw
  (the county mis-labelled them `HER Council N`; the archive normalizer both hid and mangled
  them). 2019 is now fully present.
- Turnout populated only where the source carries registered/ballots counts (2011, 2019,
  2021, 2023, 2025); older archive-slice years leave `turnout_pct` blank.
- **At-large 2007/2009** are multi-seat (`n_seats=2`) — see the convention above before
  reading `winner`/`runner_up`/`margin`.
- Precinct geometry for joins: `../geo/precinct_to_district.csv` (join `precinct` = `HER###`);
  the city's official district layer is the preferred geo source (see `../geo/`).


## 2026-07-17 — 2019 D4 primary + 2021 MAYOR primary appended (owner-approved, hand-edited)
Two rows hand-appended to `herriman_races.csv` from the 2026-07-16 SLCo re-parse:
- **2019 primary D4** (5-way) — Steven L. Shields 567 / Darryl Fenn 199 / Heather Garcia 122 /
  Kevin Allred 65 / Heather Sudweeks 50; source `2019-08-13-municipal-primary-sovc.xlsx`.
  The 2019 D4 general was already present.
- **2021 MAYOR primary** — Lorin Palmer 2,511 / Clint Smith 1,276 / Jared Esselman 1,240 /
  Nicole Grange 214; **contest-grain** from `2021-08-10-primary-election-results.pdf` (no
  precinct SOVC workbook exists for the 2021 primary), so `registered_voters`/`ballots_cast`/
  `turnout_pct` are blank.
Dated backup: `_backups/2026-07-17-audited-election-rows/herriman/`. Kearns precedent;
re-verified twice vs the county layer.
