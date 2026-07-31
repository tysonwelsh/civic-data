# election_results — Millcreek City municipal elections

Millcreek City (**Salt Lake County**, Utah) municipal **general + primary** election
results, normalized to the SLC/Sandy/South-Jordan sibling schema. Three CSVs + a
reproducible build script (`clean_elections.py`) + the retained raw county source under
`raw/`. **Do not edit the CSVs by hand — regenerate** (see "Rebuilding"). Coverage:
**2016 → 2025** (Millcreek's entire electoral history — it incorporated Dec 2016).

## Council / mayor structure

Millcreek is a **Council–Mayor** city: a **Mayor elected at-large** plus a **4-member
council elected by DISTRICT (Districts 1–4)**. The **mayor is a full voting member** of
the council (max council roll-call tally = 5). 4-year staggered terms.

Millcreek's residents voted to incorporate in Nov 2015; the **first city election was the
founding Nov 8, 2016 general** (preceded by a **June 28, 2016 primary**), and incorporation
was legally recorded Dec 28, 2016. **There is no municipal-election record before 2016 —
that short history is real, not a gap.** The stagger, as the contests appear in the county
SOVC:

| Cycle | Seats up | Years |
|---|---|---|
| **A** | **Mayor + District 1 + District 3** | 2016(founding), 2019, 2023, **2027** |
| **B** | **District 2 + District 4** | 2016(founding, short seat), 2017, 2021, 2025 |

Every seat was on the founding 2016 ballot; D2/D4 drew short initial terms and were
re-filled in 2017, landing them on the 2017/2021/2025 cycle, while Mayor/D1/D3 sit on the
2019/2023/2027 cycle.

## The mayor cycle — Jackson 2025 was an APPOINTMENT, not an election (verified)

The mayor is **not** on the 2025 ballot (Mayor is a **2027**-cycle seat). Founding mayor
**Jeff Silvestrini** served 2017–2025 (won 2016 unopposed, 2019 v. Angel Vice, 2023
uncontested). He **retired mid-term in autumn 2025 for health reasons**; on **Nov 3, 2025**
the City Council, in a special meeting, **voted unanimously to APPOINT sitting District 3
council member Cheri Jackson** to serve the ~2 remaining years of his term — Millcreek's
2nd (and first female) mayor. Jackson vacated D3; the council then appointed **Nicole
Handy** to D3. **This is a council appointment / succession, NOT an election** — there was
no 2025 (or any) Millcreek mayoral race that year, consistent with the SOVC. Logged, not
fabricated.

## Ranked-choice voting — 2021 & 2023

Millcreek joined **Utah's municipal RCV pilot in 2021 and 2023**, so those council races
were decided by instant-runoff, not plurality. The Salt Lake County SOVC carries only
**first-choice** tallies (the round-by-round tabulation is published separately), so the
`votes`/`pct` in `by_candidate` and `by_precinct` for those years are **first-choice**, and
RCV race rows are stamped `voting_method='ranked choice (RCV)'`. The race **`winner` is the
official final-round winner**, which can differ from the first-choice leader:

- **2021 District 2 — the first-choice LEADER lost.** First choice: Clark 1014, DeSirant
  988. After Bagley-Gibson and Vice were eliminated their ballots broke to DeSirant, who
  **won the final round 51.75% (≈1,080) to Clark's 48.25% (≈1,007)**. The CSV therefore
  shows Clark at `rank 1` but `is_winner=False`, and **DeSirant `is_winner=True`** — with a
  **negative first-choice `margin_votes` (−26)**, which the `ranked choice (RCV)`
  `voting_method` explains. (Round figures per rcvis.com are from a preliminary export and
  are smaller than the certified SOVC first-choice totals retained here; only the winner +
  final-round percentage are taken from them.)
- **2021 District 4** — Uipi won the final round 56.9% to Parker's 43.1% (Uipi also led
  first choice).
- **2023 District 3** — Jackson took **76% first choice = an outright round-1 majority**, so
  RCV changed nothing.

2016/2017/2019 were plurality; 2025's races each had two candidates (plurality-equivalent).

## Source

All results are **Salt Lake County Clerk** SOVC (Statement of Votes Cast) data from the
local county mirror **`~/Desktop/slco-election-archive`** — not re-scraped. Filter the
archive by the **`contest`** column (`%MILLCREEK%`), **not** the `sheet` name. Two
provenance layers are retained under `raw/`:

1. **`raw/municipal_results_long_millcreek.csv`** — the archive's canonical SOVC
   normalization (`sovc_long.csv`) filtered to Millcreek council/mayor **candidate**
   contests 2016–2025 (pre-incorporation ballot questions — 2012 INCORPORATION / COUNCIL
   DISTS, 2015 METRO TOWNSHIP-CITY / MSD — are **excluded**; they are township/formation
   questions, not council/mayor candidate races). Precinct- and vote-method-level; sums
   cleanly with **zero suppression** for **2016 (primary + general), 2017, 2023 (D3) and
   2025** — consumed straight from this slice.
2. **`raw/sovc/*.xlsx`** — the true county SOVC spreadsheets, re-parsed directly for the
   two general cycles the parsed layer does not deliver cleanly.

## The two gaps recovered from raw

| Contest | Why the archive parse missed / broke it | Recovery |
|---|---|---|
| **2019 general** (Mayor / D1 / D3) | Present only under raw **sheet codes `MIL Mayor` / `MIL Council 1` / `MIL Council 3`**, where the normalizer **lost the candidate names** (it emitted "Total"/method strings as candidates) and a `%MILLCREEK%` contest filter misses them — this is the "2019 entirely absent" gap flagged in `recon.md`. | Re-parsed `raw/sovc/2019-11-05-general-election-sovc.xlsx` (Family-A wide crosstab) for faithful candidate names + precinct totals. **All three 2019 races recovered.** |
| **2021 general** (D2 / D4) | Present but **privacy-SUPPRESSED** at the In-Person / Vote-By-Mail method split (`****` in 64/80 + 104/120 rows), destroying the precinct totals. | Re-parsed `raw/sovc/2021-11-02-general-election-sovc.xlsx` (Sheets 22/23), whose per-precinct **`Total`** sub-rows are not suppressed. |

After recovery the final CSVs have **zero suppressed cells** and every by-precinct sum
reconciles exactly to its by-candidate total (the build asserts 0 mismatches).

## The two contests that were never held — 2023 Mayor & District 1 (logged, not filled)

The "2023 D1 & Mayor missing" gap in `recon.md` is **not a data gap** — those races were
**cancelled**. In 2023 only the incumbent filed for Mayor (Silvestrini) and for District 1
(Silvia Catten), with no write-in entrants, so under Utah law (UCA 20A-1-206) Millcreek
**canceled both uncontested races** (no ballot printed, no votes counted); the incumbents
were re-elected by default. They appear in `millcreek_races.csv` as
`voting_method='uncontested (election cancelled)'` with **blank vote fields** and the
winner sourced from the city / Millcreek Journal — **no counts fabricated**, and they carry
**no precinct rows**. (2023's only counted race was District 3.)

## The 2016 mayor race was uncontested (verified)

Silvestrini won the 9-candidate June 2016 primary; the primary runner-up **Fred Healey
withdrew in Aug 2016** (cancer diagnosis), so **Silvestrini ran unopposed in the general
and took 100% (21,288 votes)**. The single-candidate raw sheet is faithful — `uncontested=
True`, not a parse defect.

## The three CSVs

- **`millcreek_races.csv`** — one row per race (**22 races: 17 general + 5 primary**,
  incl. the 2 cancelled-uncontested 2023 rows). Columns: `office`/`district`/`contest`
  (canonical) + `contest_verbatim`, `n_candidates`, `total_votes`, `winner`/`winner_votes`/
  `winner_pct`, `runner_up`/`runner_up_votes`, `margin_votes`/`margin_pct`,
  `registered_voters`/`ballots_cast`/`turnout_pct` (turnout present for 2021/2023/2025 where
  the source carries times-cast; blank for 2016/2017/2019 which carry registration but no
  ballots-cast column), `uncontested`, `suppressed_precincts` (`False` everywhere in the
  final data), `voting_method` (`plurality` / `ranked choice (RCV)` / `uncontested (election
  cancelled)`), `source_file`.
- **`millcreek_results_by_candidate.csv`** — race × candidate (**69 rows**): `votes`, `pct`,
  `rank`, `is_winner`. **For RCV rows `votes`/`pct`/`rank` are first-choice while `is_winner`
  reflects the final RCV round** (see the RCV section — 2021 D2 is the case where these
  diverge).
- **`millcreek_results_by_precinct.csv`** — precinct × candidate (**1,199 rows**). Precinct
  IDs are Salt Lake County codes (`MIL###` within the city; the citywide 2016 mayor race
  also spans neighbouring `CNR###`/`MOL###`/etc. precincts). `suppressed=True` would mark a
  redacted county cell (none survive after the 2021 raw recovery). Cancelled 2023 races have
  no rows here.

## Name normalization

`norm_name()` normalizes each candidate name **alongside** the verbatim source value (never
overwrites raw): collapses whitespace, strips the `(NON)` / `(NP)` non-partisan tag and the
leading `*` write-in mark, and canonicalizes write-ins. Election names are UPPER-CASE; to
join elections ↔ votes ↔ comments on person + year + district, further strip case/suffixes
(council `all_votes.csv` names are mixed-case — note Jackson appears as `CHERI M. JACKSON`
in 2016 and `CHERI JACKSON` later).

## Verification / cross-checks (external)

- **Founding 2016 general winners all confirmed** against contemporaneous reporting
  (Deseret News / SL Tribune): D1 **Silvia Catten**, D2 **Dwight Marchant**, D3 **Cheri
  (M.) Jackson**, D4 **Bev Uipi**, Mayor **Jeff Silvestrini** (unopposed).
- **Current roster reconciles**: Mayor **Cheri Jackson** (D3 2016/2019/2023 → mayor by 2025
  appointment), D1 **Silvia Catten** (2016/2019/2023), D2 **Thom DeSirant** (2025; the 2021
  D2 RCV winner too), D3 **Nicole Handy** (appointed 2025 when Jackson became mayor), D4
  **Bev Uipi** (2016/2017/2021/2025).
- **2021 D2 RCV upset** (DeSirant over first-choice leader Clark, 51.75–48.25 final) and the
  **2025 mayoral appointment** verified via SL Tribune / Deseret News / KSL / Millcreek
  Journal.

## Rebuilding

```
cd election_results && python3 clean_elections.py            # reads raw/, writes the 3 CSVs
                       python3 clean_elections.py --report    # + per-race summary
```
Idempotent; asserts zero precinct/candidate reconciliation mismatches. Re-run when a **new
cycle** posts to the county site: add its SOVC to the archive, refresh the slice
(`raw/municipal_results_long_millcreek.csv`) if the archive normalizer covers it cleanly, or
add a raw parser call (mirror `parse_2019`/`parse_2021`). Mind the cycle (A = Mayor/D1/D3,
B = D2/D4) and whether the city is still using RCV that year.

## Gaps / caveats

- **No pre-2016 record** — Millcreek did not exist; not a gap.
- **2019** fully recovered from raw (Mayor, D1-uncontested, D3); the archive's normalized
  layer for 2019 is unusable (lost candidate names) — always rebuild 2019 from `raw/sovc/`.
- **2023 Mayor + D1 were cancelled** (uncontested) — no vote data exists (blank race rows).
- **RCV first-choice caveat** (2021 + 2023): by-candidate/by-precinct counts are
  first-choice; the seat `winner` is the final-round winner (2021 D2 diverges).
- **Turnout** blank for 2016/2017/2019 (source carries registration but no ballots-cast).
- Precinct geometry for joins: `~/Desktop/slco-election-archive/geo/` and the city's own
  council-district layer (see `../geo/`; note the published layer is the **2022–2032**
  redistricting vintage — pre-2022 elections used the original 2016 lines).
