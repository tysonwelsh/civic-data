# Orem (Utah) Municipal Election Results

Utah County (UGRC CountyID **25**) administers Orem's elections. This folder holds the
county source files (in `raw/`, never edited) filtered to **Orem Mayor + Orem City Council
races only** and normalized for analysis. Covers the four odd-year cycles
**2019, 2021, 2023, 2025** (members seated 2020+).

> **Disambiguation:** Orem, **Utah County, Utah**. The Utah County source files are
> county-wide and list every city; only contests whose name contains `Orem` are kept.
> Neighboring Utah County cities (Provo, Lehi, Pleasant Grove, Spanish Fork, Salem,
> Santaquin, American Fork, Lindon, Vineyard, etc.) are excluded.

## Council structure — ALL AT-LARGE (vote-for-N)

Orem = **6 council members + 1 Mayor, ALL ELECTED CITYWIDE / AT-LARGE — NO DISTRICTS**
(council-manager, nonpartisan; confirmed orem.gov/citycouncil + recon §2). 4-yr staggered
terms: **3 council seats up each odd year**; Mayor on a separate 4-yr cycle (elected 2017,
2021, 2025 — so **no mayor race in 2019 or 2023**).

City Council runs as **one multi-winner field per cycle** — all candidates appear in the
single `Orem City Council` contest and the **top N vote-getters win the N open seats**
("Vote For 3" on every official county PDF here → **N = 3** in all four cycles). Mayor is a
conventional single-winner race.

## Pipeline

```
raw/*.csv  raw/*.pdf            Utah County SOURCE OF TRUTH (all cities/county)
clean_elections.py             filter to Orem council+mayor, unpivot crosstab, rank, aggregate
  -> orem_results_by_precinct.csv  precinct x candidate (CSV cycles only: 2021, 2025)
  -> orem_results_by_candidate.csv race x candidate: votes, pct, rank, is_winner
  -> orem_races.csv                ONE ROW PER RACE: winner, runner-up, seat-margin, turnout
```

Regenerate: `python3 clean_elections.py`. **Totals: 11 races, 75 candidate rows, 2,063 precinct rows.**

## Sources used (re-scraped from `vote.utahcounty.gov/results/<year>`; hashed `/cms/uploads/` names)

| Cycle | General | Primary | In `raw/` |
|---|---|---|---|
| **2019** | **PDF only** (citywide) | **PDF only** (citywide) | `2019_General_Results_PDF_a69d246ddc.pdf`, `2019_Primary_Results_PDF_dba3744ad0.pdf` |
| **2021** | **SOVC CSV** (precinct) | **SOVC CSV** (precinct) | `21_G_Countywide_SOVC_suppressed_1b85ad469d.csv`, `21_PP_2021_Primary_Statement_of_Votes_Cast_SUPPRESSED_bd47a35ddf.csv` |
| **2023** | **PDF only** (citywide) | **PDF only** (citywide) | `2023_General_voting_results_be47c5636c.pdf`, `2023_Primary_voting_results_30a0ba993f.pdf` |
| **2025** | **SOVC CSV** (precinct) | **SOVC CSV** (precinct, council only — no mayor primary) | `SOVC_Simple_Redacted_7a5eddcaf2.csv`, `2025_Primary_SOVC_suppressed_4bc086dabf.csv`; `OFFICIAL_Countywide_Results_11_17_f09d22f26a.pdf` (cross-check) |

Live source URLs (verified 2026-06):
- 2025 general SOVC: `https://vote.utahcounty.gov/cms/uploads/SOVC_Simple_Redacted_7a5eddcaf2.csv`
- 2025 primary SOVC: `https://vote.utahcounty.gov/cms/uploads/2025_Primary_SOVC_suppressed_4bc086dabf.csv`
- 2021 general SOVC: `https://vote.utahcounty.gov/cms/uploads/21_G_Countywide_SOVC_suppressed_1b85ad469d.csv`
- 2021 primary SOVC: `https://vote.utahcounty.gov/cms/uploads/21_PP_2021_Primary_Statement_of_Votes_Cast_SUPPRESSED_bd47a35ddf.csv`
- 2023 general PDF: `https://vote.utahcounty.gov/cms/uploads/2023_General_voting_results_be47c5636c.pdf`
- 2023 primary PDF: `https://vote.utahcounty.gov/cms/uploads/2023_Primary_voting_results_30a0ba993f.pdf`
- 2019 general PDF: `https://vote.utahcounty.gov/cms/uploads/2019_General_Results_PDF_a69d246ddc.pdf`
- 2019 primary PDF: `https://vote.utahcounty.gov/cms/uploads/2019_Primary_Results_PDF_dba3744ad0.pdf`
- 2025 general countywide (cross-check): `https://vote.utahcounty.gov/cms/uploads/OFFICIAL_Countywide_Results_11_17_f09d22f26a.pdf`

All 9 raw files re-verified 2026-07-19: each URL returned HTTP 200 and was confirmed
**byte-identical (md5)** to the stored `raw/` copy.

> Filename hashes are unguessable: always re-scrape the `/results/<year>` index and regex
> `/cms/uploads/[^"']+`. (These are the same county-wide files Provo's build used.)

## The wide-crosstab unpivot (the tricky part)

Utah County SOVC CSVs are a **wide crosstab**: one row per precinct; each *contest×candidate*
is its own column, with a multi-row header spanning those columns:
- **2-row header** (2021 general): row 0 = contest (repeated across its candidate columns),
  row 1 = candidate.
- **3-row header** (2021 primary, 2025 general + primary): row 0 = contest, row 1 = party
  (`NON`, non-partisan — ignored), row 2 = candidate.

`parse_sovc_csv()` reads the contest row + the **last** header row, keeps only columns whose
contest normalizes to an Orem Mayor/Council race, then sums each Orem precinct row into both
citywide totals and per-precinct rows.

**Precinct codes / column index differ by file** (reconciled):
- 2021 **general**: precinct code in **col 0**, prefix `OR##` (52 Orem precincts).
- 2021 **primary**, 2025 **general + primary**: precinct code in **col 2** (col 0/1 are
  county number / sequence), prefix `25OR##`. The `25` county prefix is stripped →
  canonical `OR##`, matching the UGRC VistaBallotAreas `25OR##` family (recon §5).
- **Dropped pseudo-candidates:** `OVER VOTES`, `UNDER VOTES`, `VOTERS`, `BALLOTS CAST`,
  `Total`, `Contest Totals`. **Kept:** `WRITE-IN` (real candidate column; e.g. 2025 council
  had 195 write-ins).
- Look-alike Utah County cities excluded by the `"orem" in contest` match.

Precinct sums reconcile **exactly** to citywide totals (verified 2021 + 2025 general council,
e.g. 2025 Mecham 9,474 / Muhlestein 9,102 / Millett 9,077 — precinct-sum == county ZZZ row).

## AT-LARGE MODELING DECISION (important)

- `district` column = `At-Large` for all council races (empty for Mayor).
- A council "race" has **multiple winners**. In `orem_results_by_candidate.csv`,
  `is_winner = Y` for `rank <= N` (general; N = 3). For **primaries**, `is_winner = Y`
  means **advanced to the general** = top `2N` = top 6 (mayor primary advances top 2).
- `total_votes` for a council race is the **sum of all candidate votes**, larger than ballots
  cast because each voter may pick up to N candidates. So candidate `pct` = **share of all
  council votes cast**, NOT turnout. (Mayor `pct` is normal. For turnout use the Mayor race
  or the raw `BALLOTS CAST` columns.)
- In `orem_races.csv` (one row per race), for a multi-winner council field:
  `winner` = top vote-getter; `runner_up` = the candidate at **rank N+1** (first loser — just
  missed the last seat); `margin_votes`/`margin_pct` = **rank-N winner minus rank-(N+1)
  loser**, i.e. the margin that **decided the final seat** — the analytically meaningful
  "closeness" of an at-large race. (Mayor: usual 1st-vs-2nd.) For a primary, `runner_up`/
  `margin` describe the **advancement cutoff** (rank 2N vs 2N+1).

## 2019 + 2023 PDF-only gap

- **2019 and 2023 published NO Orem SOVC CSV — only born-digital rollup PDFs** giving
  **citywide totals only**. So **`orem_results_by_precinct.csv` contains 2021 + 2025 only**
  (2019 and 2023 have NO precinct-level Orem data). Same blocker Provo hit.
- The citywide totals for 2019 + 2023 (primary + general) are hand-transcribed from the
  official Utah County PDFs into `PDF_CITYWIDE` in `clean_elections.py`, each value verified
  against the `pdftotext -layout` extraction.
- The state portal `electionresults.utah.gov` (Enhanced Voting) carries 2023/2025 Orem
  ballot-item dashboards as an alternate, but was not needed — the county PDFs are
  authoritative and complete for the citywide figures.

## Coverage (11 races)

| Year | Type | Office | N (Vote For / advance) | Winners / advancers |
|---|---|---|---|---|
| 2019 | primary | Council | 3 (adv 6) | Peterson, Lauret, Lentz, Lambson, Rands, N. Jensen advance |
| 2019 | general | Council | 3 | **Peterson, Lambson, Lauret** (Lentz missed by 12 — Lauret 6,740 vs Lentz 6,728) |
| 2021 | primary | Mayor | 1 (adv 2) | Evans, Young advance |
| 2021 | primary | Council | 3 (adv 6) | Millett, Spencer, Macdonald, Mecham, Zundel, N. Jensen advance |
| 2021 | general | Mayor | 1 | **David A. Young** (beat Jim Evans) |
| 2021 | general | Council | 3 | **Millett, Spencer, Macdonald** |
| 2023 | primary | Council | 3 (adv 6) | Lambson, Gale, Killpack, Muhlestein, McKell, Rands advance |
| 2023 | general | Council | 3 | **Lambson, Gale, Killpack** (Killpack 8,457 over Muhlestein 7,994 for seat 3) |
| 2025 | primary | Council | 3 (adv 6) | Mecham, Moulton, Mortimer, Millett, Muhlestein, Spencer advance |
| 2025 | general | Mayor | 1 | **Karen McCandless** (beat incumbent Dave Young, 9,574–9,056) |
| 2025 | general | Council | 3 | **Mecham, Muhlestein, Millett** (Millett 9,077 over Spencer 8,789 for seat 3) |

No mayoral race in 2019 or 2023 (mayor is 4-yr, elected 2017/2021/2025). 2025 had **no mayor
primary** (only 2 mayor candidates → no primary needed).

## Cross-check (external corroboration)

Winners independently verified — all consistent with the certified data here:
- **2025 Mayor:** Daily Herald (heraldextra.com) + KSL: **Karen McCandless** beat incumbent
  **Dave Young** 52.8%–47.2% (certified 9,574 vs 9,056). Wikipedia "Orem, Utah" lists
  McCandless as current mayor.
- **2025 Council:** certified winners **Mecham, Muhlestein, Millett** (recon §2 roster +
  Wikipedia). **Note:** election-NIGHT unofficial counts (KSL 11/5) had Mortimer & Moulton
  ahead of Millett & Spencer for seats 2–3; the **certified county SOVC** (this repo's source
  of truth) seats Muhlestein (9,102) and Millett (9,077) over Mortimer (8,628)/Moulton
  (8,557). Use certified.
- **2023 Council:** Daily Herald ("Lambson, Gale, Killpack lead in Orem City Council race") +
  KSL: **Lambson, Gale, Killpack** win; totals match exactly (9,098 / 8,606 / 8,457).
- **2021:** Mayor **David A. Young**; council **Millett, Spencer, Macdonald** (recon §2: the
  2021 cohort = Spencer, Lauret, Macdonald, Peterson held 2022–2026 seats; Lauret/Peterson
  were the 2019 winners on the other stagger; consistent).
- **2019:** **Peterson, Lambson, Lauret** (Lambson re-elected 2nd term in 2023; consistent
  with the orem.gov roster).

## Connecting to the rest of the repo

Elections are point-in-time events (odd-year Nov) — not part of weekly `../weeks/` bundles.
They join to the rest of the repo via **person + year**: a race winner becomes a
councilmember whose roll-call votes live in `../meeting_minutes/all_votes.csv`. Candidate
names here are UPPER-CASE (`LANAE MILLETT`) vs mixed-case in votes/roster data
(`LaNae Millett`); normalize case + reconcile spelling drift (Millet/Millett,
Macdonald/MacDonald, Debby/Debbie Lauret) before joining. `WRITE-IN` is an aggregate, not a
person. Because Orem is **entirely at-large**, there is **no precinct→district map** — it is
the identity map; every Orem precinct elects the same 7 citywide officials. The address tool
degenerates to an in/out-of-city-limits check.

## Gaps / caveats

- **2019 + 2023 = no precinct data** (PDF rollup only) → `orem_results_by_precinct.csv` is
  2021 + 2025 only. Citywide totals for 2019/2023 are complete and externally verified.
- Vote-for-N inflates council `total_votes`; `pct` is share-of-council-votes, not turnout.
- 2025-night unofficial vs certified seat order differs (see cross-check) — repo uses
  certified county SOVC.
- Files carry "suppressed/redacted" in their names (small-precinct privacy suppression); the
  per-precinct rows nonetheless sum exactly to the certified county totals for all CSV races.

## Don't
- Don't edit the raw `vote.utahcounty.gov` files.
- Don't treat `OVER VOTES`/`UNDER VOTES`/`Total`/`Contest Totals` as candidates (keep `WRITE-IN`).
- Don't read a council race as single-winner — top 3 win (at-large vote-for-N).
- Don't match a neighboring Utah County city (Provo, Lehi, Pleasant Grove, etc.) as Orem.
- Don't expect 2019/2023 precinct rows — those cycles are PDF-only (citywide).
