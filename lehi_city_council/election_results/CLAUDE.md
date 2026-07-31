# Lehi (Utah) Municipal Election Results

Utah County (UGRC CountyID **25**) municipal election results, filtered to **Lehi City
Mayor + City Council races only** and normalized for analysis. Covers the municipal cycles
**2019, 2021, 2023, 2025**.

> **Disambiguation:** Lehi, **UTAH** (Utah County, "Silicon Slopes"). All contests carry the
> literal ballot names `Lehi Mayor` / `Lehi City Council`. Watch for neighboring Utah County
> cities in the same source files (Alpine, American Fork, Eagle Mountain, Saratoga Springs,
> etc.) — only `Lehi`-named contests / `LE`-prefixed precincts are kept.

## Council structure — AT-LARGE, seat-numbered NONE

Lehi is a **six-member form-of-government** city: **Mayor + 5 Council Members, all elected
AT-LARGE** (no geographic districts), 4-year **staggered** terms (alternating ~3-seat and
~2-seat cycles). Council candidates run in **one citywide `Lehi City Council` field**; the
**top-N vote-getters win the N open seats** — the ballot does NOT use numbered seats in these
cycles. Mayor is a single-winner citywide race on the 2017/2021/2025 cycle (so **no mayor
race in 2019 or 2023**).

- `district = At-Large` for all council rows; empty for Mayor.
- Seats up per cycle: **2019 = 3**, **2021 = 2**, **2023 = 3**, **2025 = 2**.
- `total_first_choice_votes` for a council race is the **sum of candidate first-choice / vote
  totals**, which for a vote-for-N field is **inflated** (each voter may mark up to N). So
  council `*_pct` = a candidate's **share of all council votes**, NOT turnout. Use the Mayor
  race (vote-for-1) for a turnout-like denominator.

## TWO tabulation methods — the central branch

| Cycle | Method | Notes | Numeric source |
|---|---|---|---|
| **2019** | **Plurality** (vote-for-3) | 6 candidates = 2×seats, so no primary | Utah County certified results PDF |
| **2021** | **Ranked-Choice Voting** | Lehi's FIRST RCV year; **RCV replaced the primary** (none held) | Utah County certified SOVC CSV (first-choice + precincts) + rcvis / Lehi Free Press (final rounds) |
| **2023** | **Ranked-Choice Voting + revived Aug primary** | The Corey **Astill** mid-count withdrawal + recount happened in the **primary** | state Enhanced Voting portal (certified first-choice + precincts) + rcvis (rounds) |
| **2025** | **Plurality** (Lehi dropped RCV) + Aug primary | mayor + council both plurality | state Enhanced Voting portal JSON (citywide + precincts) |

`voting_method` column = `plurality` or `RCV`. `election_type` = `municipal general` /
`municipal primary`.

## How winner / runner_up / margin are defined (multi-seat at-large)

For a multi-seat at-large race the race-row uses the **ranking metric** (`round1` =
first-choice for RCV, total votes for plurality):

- `winner` = **top vote-getter** (rank 1).
- `runner_up` = **first loser** = the highest-ranked candidate who did **not** win a seat
  (excluding any *withdrawn* candidate — see 2023 primary).
- `margin_votes` = **(lowest-ranked winner) − (first loser)** = the **seat-deciding margin**
  (rank N vs rank N+1). `margin_pct` uses `total_first_choice_votes` as denominator.

In **every Lehi cycle the RCV round-by-round winner SET equals the top-N first-choice set**
(RCV did not change who won), so `is_winner` = top-N — except the 2023 primary (Astill).
**Every** seat winner is flagged `is_winner=True` (a 2-seat race has two True rows, a 3-seat
race three). For RCV winners, `final_votes` carries the **final-round** total; blank for
plurality and for non-winners.

## RCV handling per cycle

### 2021 council (vote-for-2, sequential RCV) — winners CONDIE & HANCOCK
First-choice from the certified Utah County **SOVC** (`uc_2021_general_SOVC.csv`,
"Lehi City Council 1st Choice" county-totals row): Condie 2300, Hancock 1811, Miles 1376,
Kunze 1291, Bullen 1134, McIntosh 1108, Purtschert 1003, Hamilton 524, Erickson 355.
Sequential multi-seat RCV elected **Chris Condie** (seat 1) and **Paul Hancock** (seat 2).
Final-round winner totals (`final_votes`): **Condie 3,073 (R8)**, **Hancock 2,583 (R7)**,
from the **Lehi Free Press** 2021-11-02 certified report.

> **rcvis doubling artifact (flagged):** the rcvis pages `21g_le_cc_1_u4` / `21g_le_cc_2_u2`
> (mirrored in `raw/rcvis_2021_council_seat*.html`) render **DOUBLED** cumulative final
> totals (Condie 6,167 / Hancock 5,466 — exactly ~2× the certified 3,073 / 2,583). Their
> **round-1** values match the certified SOVC exactly, but their final cumulatives do not.
> This repo uses the **certified press finals (3,073 / 2,583)**, not the rcvis finals.

### 2021 mayor — winner JOHNSON
Only **2 candidates** (Mark I. Johnson 6,994 vs Jesse L. Riddle 4,295), so RCV resolved on
the **first count** (1 round); `final_votes` = first-choice for the winner. (A web summary
reporting 3,425 / 2,056 is a partial early count; the certified SOVC 6,994 / 4,295 is used.)

### 2023 general (vote-for-3, RCV) — winners STALLINGS, ALBRECHT, NEWALL
First-choice + precincts from the **state Enhanced Voting certified portal**
(`ev_2023_general_ballot-items.json`, "Lehi City Council 1st Choice"): Stallings 2,096,
Albrecht 1,754, Newall 1,467, Kunze 1,121, Roberts 1,048, Glade 699 (8,185 ballots). This
EV count is **turnout-validated** (8,185 council ballots ≈ the 2019 council's ~8,143).
Winners (top-3, confirmed by the **Lehi Free Press** 2023-11-21 certification report and the
rcvis round tabulations): **Michelle Stallings, Paige Albrecht (re-elected), Heather
Newall**. `final_votes` = the rcvis final-round totals **Albrecht 2,973 / Stallings 2,917 /
Newall 2,863** (from `raw/rcvis_2023_council_seat*.html`).

> **2023 EV-vs-rcvis first-choice discrepancy (flagged):** rcvis's 2023 general pages
> tabulated an **earlier, smaller canvass** (~6,335 first-choice ballots) than the final
> certified EV count (8,185). The `final_votes` (2,973 etc.) come from that rcvis snapshot,
> so they reflect the **RCV outcome on a smaller ballot universe** than the `round1_votes`
> (final EV canvass); the **winner set is identical** either way. We use EV for first-choice
> + precincts (most certified) and rcvis only for the round-by-round final figures.

### 2023 primary (Aug 2023) — the Astill withdrawal + recount
Council vote-for-3 ⇒ **top 6 advance**. 15 candidates ran. Candidate **Corey Astill** led on
first choice at **rank 4** (371) but **withdrew mid-count** to run for the state Senate. Per
Lt. Governor guidance (Election Code 20A-4-603(5)) the city **recounted WITHOUT Astill** and
advanced the **top 6**: **Albrecht, Stallings, Newall, Kunze, Roberts, and K. Casey Glade**
(Glade advanced in Astill's place). Source: `raw/rcvis_2023_council_primary_astill.html`.
In the data, Astill is `is_winner=False` and **excluded from the runner-up/margin** boundary
(so `runner_up` = Jason Hill, the first true non-advancer, not Astill). First-choice values
are from rcvis; the certified advancement was decided by RCV elimination rounds, so the
primary `margin` is nominal (first-choice boundary) — the **event**, not the margin, is the
point.

## Plurality cycles

- **2019 general** (council vote-for-3, `uc_2019_general_results.pdf`): **Paige Albrecht
  5,250 / Mike V Southwick 4,135 / Katie Koivisto 3,969** win; Hemmert 3,763 (first loser),
  Black 3,711, Revill 3,602. No mayor race; 6 candidates = 2×seats so **no primary**.
- **2025 primary** (Aug 12, Enhanced Voting): Mayor vote-for-1, 4 candidates → top 2 advance
  (**Albrecht, Binns**); Council vote-for-2, 10 candidates → top 4 advance (**Lockhart,
  Freeman, Harrison, Peterson**). `is_winner=True` = advanced.
- **2025 general** (Nov 4, Enhanced Voting): **Mayor — Paul Binns** 7,909 (53.5%) over Paige
  Albrecht 6,873. **Council (vote-for-2) — James Harrison** 7,603 and **Rachel Freeman**
  7,163 win; Emily Lockhart 6,972 (first loser, seat-deciding margin 191), Jared V. Peterson
  5,982.

## Sources (all mirrored verbatim into `raw/`)

**State Enhanced Voting certified portal** (`electionresults.utah.gov`, API base
`…/results/public/api/elections/utah-county-ut/<slug>/…`):
| File | Slug | Covers |
|---|---|---|
| `ev_2023_general_ballot-items.json` | `2023-Nov-General` | Lehi council 1st–6th-choice tallies (certified first-choice) |
| `ev_2023_general_council_1stchoice_detail.json` | `2023-Nov-General` | Lehi council 1st-choice + 43-precinct breakdown |
| `ev_2025_general_ballot-items.json` | `general11042025` | 2025 general contest list (incl. Lehi mayor + council) |
| `ev_2025_general_mayor_detail.json` / `_council_detail.json` | `general11042025` | Lehi mayor / council + 55-precinct breakdowns |
| `ev_2025_primary_ballot-items.json` | `primary08122025` | 2025 primary contest list |
| `ev_2025_primary_mayor_detail.json` / `_council_detail.json` | `primary08122025` | Lehi mayor / council primary + precinct breakdowns |

(The EV portal hosts **2023 and 2025** for Utah County; querying it for **2019/2021** slugs
returns 404 — those predate the state's migration to Enhanced Voting.)

**Utah County results portal** (`vote.utahcounty.gov/results/<year>`, hashed `/cms/uploads/`
filenames — index pages also saved as `utahcounty_results_index_*.html`):
| File | Covers |
|---|---|
| `uc_2019_general_results.pdf` | 2019 OFFICIAL countywide results — "Lehi City Council / Vote For 3" |
| `uc_2019_general_precinct_SOVC.pdf` | 2019 countywide precinct SOVC (22 MB, suppressed; not parsed — see Gaps) |
| `uc_2021_general_SOVC.csv` | 2021 certified Statement of Votes Cast — Lehi mayor + council 1st-choice **per precinct** |
| `uc_2021_general_results.pdf` | 2021 results summary (cross-ref) |
| `uc_2023_general_results.pdf` | 2023 countywide results — **excludes RCV cities like Lehi** (kept for provenance) |

**rcvis.com round-by-round RCV tabulations:**
| File | rcvis slug | Covers |
|---|---|---|
| `rcvis_2021_council_seat1_condie.html` | `21g_le_cc_1_u4` | 2021 council seat 1 (Condie wins R8) — finals DOUBLED, see note |
| `rcvis_2021_council_seat2_hancock.html` | `21g_le_cc_2_u2` | 2021 council seat 2 (Hancock wins R7) — finals DOUBLED |
| `rcvis_2023_council_seat1_albrecht.html` | `2023-lehi-city-council` | 2023 full field, Albrecht wins seat 1 (final 2,973) |
| `rcvis_2023_council_seat3_newall.html` | `2023-lehi-city-council-2` | 2023 (Albrecht+Stallings removed), Newall wins (final 2,863) |
| `rcvis_2023_council_fullfield_update.html` | `2023-lehi-city-council-3` | 2023 full-field, later canvass update |
| `rcvis_2023_council_primary_astill.html` | `2023-lehi-city-council-primary` | 2023 primary, 15 candidates incl. Astill |

External corroboration (winners, not stored): **Lehi Free Press** (2021-11-02 "Voters reelect
Johnson, Condie and Hancock"; 2023-11-21 "Albrecht wins re-election, Stallings and Newall
elected"), **Daily Herald / KSL / Deseret News** (2023 Astill recount), Lehi City elected-
officials page, and the repo `recon.md` (current officeholders).

## Pipeline

```
raw/ev_*.json          Enhanced Voting JSON (2023 first-choice+precincts; 2025 all + precincts)
raw/uc_2021_*SOVC.csv  Utah County certified SOVC (2021 first-choice + Lehi precincts)
raw/uc_2019_*results.pdf  Utah County certified PDF (2019 council citywide)
raw/rcvis_*.html       RCV round tabulations (transcribed finals: 2021, 2023)
clean_elections.py     branch on method, normalize, rank, flag winners, aggregate
  -> lehi_races.csv                 ONE ROW PER RACE: winner, runner-up, seat-deciding margin
  -> lehi_results_by_candidate.csv  race × candidate: round1 votes/pct, final_votes, rank, is_winner
  -> lehi_results_by_precinct.csv   precinct × candidate (first-choice for RCV)
```
Regenerate: `python3 clean_elections.py` → **9 races, 58 candidate rows, 1,688 precinct rows**.
RCV finals + the 2019/2021/2023 citywide figures are **transcribed constants** (each annotated
with its source file); 2025 + the precinct breakdowns are read directly from the raw files.

## Precinct data

- **2025 (plurality): full granularity** — EV `breakdownResults`, precinct codes `25LE##`
  (CountyID 25 + `LE` + ##); all four 2025 contests (general mayor/council + primary
  mayor/council). Sums tie to citywide within ~0.1% (a handful of mail/provisional ballots
  not split out by precinct).
- **2021 (RCV): first-choice per precinct** — from the certified SOVC, 30 Lehi precincts
  (`LE01`–`LE27` incl. split-precinct `…S`), normalized to `25LE##`. Precinct sums ≈ citywide
  first-choice (Condie 2,298 vs 2,300 — a couple ballots sit in cross-coded precincts).
- **2023 (RCV): first-choice per precinct** — from the EV certified portal (43 precincts).
  These are the **EV** first-choice counts (citywide 8,185); do **not** sum them against the
  rcvis `final_votes`, which are from an earlier canvass (see the 2023 discrepancy note).
- **Gaps:** 2019 has **no precinct breakdown** here (only a 22 MB suppressed countywide PDF;
  citywide totals used). The **2021/2023 RCV rounds are citywide only** (rcvis publishes no
  per-precinct rounds). The **2023 primary** is citywide only (rcvis).

## Connecting to the rest of the repo

Elections are point-in-time odd-November events (not weekly `../weeks/` material). They join
the rest of the repo via **person + year**: a race winner becomes a councilmember whose
roll-call votes live in `../meeting_minutes/`. Candidate names here are UPPER-CASE (e.g.
`RACHEL FREEMAN`) vs mixed-case ("Councilor Freeman") in the minutes — normalize case before
joining. Because Lehi is **at-large**, there is no precinct→district map (it's identity):
every Lehi precinct (`25LE##`) elects the same citywide officials.

Cross-walk to current officeholders (recon.md): **2025** winners Binns (Mayor), Harrison &
Freeman (council, terms to Jan 2030); **2023** winners Stallings & Newall (to Jan 2028) +
Albrecht (later vacated → Emily **Lockhart** appointed interim to 2028; Lockhart then lost the
2025 council race); **2021** winners Johnson (Mayor) + Condie & Hancock (terms to 2025/26,
replaced by the 2025 council winners).

## Don't
- Don't treat Lehi council as district-based — it is **at-large** (no numbered seats in these
  cycles). `district` is always `At-Large` (council) or empty (mayor).
- Don't read a multi-seat council `winner` as the only victor — **all** top-N are
  `is_winner=True` (2019 & 2023 each have 3 winners; 2021 & 2025 each have 2).
- Don't use the **rcvis 2021 final cumulatives** (6,167 / 5,466) — they're doubled; the
  certified finals are **3,073 / 2,583**.
- Don't sum the **2023 EV precinct** first-choice against the **rcvis `final_votes`** — they
  are from different canvass snapshots (8,185 vs ~6,335).
- Don't read Corey **Astill** as a 2023-primary loser-by-vote — he **withdrew** mid-count;
  the recount advanced Glade in his place.
- Don't treat council `total_first_choice_votes` as turnout (vote-for-N inflation) — use the
  Mayor race for a turnout denominator.
- Don't expect a 2019 mayor or 2023 mayor race — Mayor is on the 2017/2021/2025 cycle.
