# election_results — Town of Alta municipal elections

Town of Alta (**Salt Lake County**, Utah) municipal **general** election results, normalized
to the SLC/Sandy sibling schema. Three CSVs + a reproducible build script
(`clean_elections.py`) + the retained raw county-source slice under `raw/`.
**Do not edit the CSVs by hand — regenerate** (see "Rebuilding").

## Council / mayor structure — AT-LARGE town, the Mayor VOTES

Alta uses Utah's **Town** form of government: a town-wide (VOTING) **Mayor** plus a **4-member
Town Council, ALL elected AT-LARGE** — there are **no council districts**. Non-partisan,
staggered 4-year terms, so each odd-year general fills **2 at-large council seats** (plus the
Mayor on the mayoral cycle). Because seats are at-large, a `district` value of `At-Large` is
carried on every council row (the Mayor row's `district` is blank). Data floor **2020** → the
in-scope generals are **2021** and **2023**.

## Source

All results derive from the **canonical Salt Lake County Clerk SOVC** (Statement of Votes Cast)
long file — `salt_lake_county/elections/slco_municipal_results_long.csv` — **not re-scraped**.
Since the **2026-07-19 re-point**, `clean_elections.py` reads that county canonical **directly**
(filtered in-code to the **GENUINE Town-of-Alta contests only** — `TOWN OF ALTA COUNCIL
AT-LARGE` / `TOWN OF ALTA MAYOR`); the old redundant per-city slice copy
(`raw/municipal_results_long_alta.csv`) was **retired**.

**⚠ The `ALTA CANYON REC …` contests are EXCLUDED.** The **Alta Canyon Recreation Special
Service District** (a Sandy/Cottonwood-Heights-area rec district) is a **different entity — NOT
the Town of Alta**. `clean_elections.py` drops anything with the CANYON token (and the workbook
`Cumulative` rollup rows), and `alta_races.csv` contains **0** canyon rows (verified; the county
file carries ALTA CANYON REC BOARD / SERVICE DIST contests 2007–2013 — none appear in the Alta
data).

**Only ≥2020-floor Town-of-Alta contests are built.** The county long file spans 2007–2025; the
build reads only `year >= 2020` Town-of-Alta contests. Earlier Alta contests stay in the
canonical for provenance but are not written to the derived tables.

## The two data realities in scope

| Cycle | Contest(s) | Reality |
|---|---|---|
| **2023 general** | Council At-Large (2 seats) | Real per-precinct counts, **no suppression** — summed straight from the long file (Morgan 66 & Schilling 51 won; Davis 42 first loser). |
| **2021 general** | Mayor + Council At-Large | The county originally **SUPPRESSED every candidate tally** (`**** — INSUFFICIENT TURNOUT TO PROTECT VOTER PRIVACY`; Alta's ~380-person precinct is below the privacy floor). **RECOVERED 2026-07-19:** the upstream family-C Total-recovery fix released each precinct's own un-suppressed `vote_method='Total'` sub-row, so the real tallies are now filled from the county's own Totals. The In-Person / Vote-By-Mail method **split remains county-suppressed** (that granularity was never released), and the `note` records the recovery provenance. Never fabricated — the counts are the county's released Totals. |

**2021 recovered tallies (county-released Totals, 2026-07-19):** Council — **John Byrne 73** &
**Carolyn Anctil 59** won; **Margaret E. Bourke 53** did not (2 seats; margin = last winning
seat − first loser = 59 − 53 = 6). Mayor — **Roger Bourke 85**, unopposed (Harris Sondak
withdrew). These agree with the prior external cross-check (Deseret News / ABC4 / Town canvass
notice), which had lower unofficial estimates; the certified county Totals supersede them.

## At-large multi-seat convention (matches sandy/logan/nephi siblings)

For a vote-for-N at-large council race:
- `winner` = top vote-getter; `is_winner=True` for the top **`n_seats`** candidates.
- `runner_up` = **first loser** (highest-polling non-winner).
- `margin_votes` = **(last winning seat) − (first loser)** (e.g. 2023: Schilling 51 − Davis 42 = 9).
- `note` names every seat filled and states the margin convention.

## 2025 municipal election — KNOWN GAP (pending)

The **Nov-2025 SLCo general SOVC contains NO Alta contest at all** (verified) — so the 2025 cycle
is **not yet in the canonical county file**. But the election **did occur**: per the 2026 council
minutes, **Craig Heimark won a council seat** (he is seated 2026→). This is a **county-file
acquisition lag, not a Town gap** — re-pull the raw 2025 SOVC when the county posts Alta and add
it to `alta_races.csv`. Tracked in the repo-root `TODO.md`.

## The three CSVs

- **`alta_races.csv`** — one row per race (**3 races**: 2021 Council At-Large + 2021 Mayor +
  2023 Council At-Large). Columns include `office`/`district`/`contest` (canonical) +
  `contest_verbatim`, `n_seats`, `n_candidates`, `voting_method`
  (`plurality` / `plurality at-large (vote-for-2)`), `total_first_choice_votes`,
  `winner`/`winner_votes`/`winner_pct`, `runner_up`/`runner_up_votes`,
  `margin_votes`/`margin_pct`, `registered_voters`/`ballots_cast`/`turnout_pct`, `uncontested`,
  `suppressed_precincts`, `note`, `source_file`. 2021 numeric fields are **filled from the
  county-released Totals** (recovered 2026-07-19); `suppressed_precincts` is now blank for 2021.
- **`alta_results_by_candidate.csv`** — race × candidate (**7 rows**): `votes`, `pct`, `rank`,
  `is_winner`. 2021 + 2023 populated (2021 recovered 2026-07-19).
- **`alta_results_by_precinct.csv`** — precinct × candidate. Precinct IDs are `ALT001` (the Town
  precinct). `suppressed=True` marks a still-redacted county cell — after the 2021 recovery the
  precinct Totals are released, so **no `suppressed=True` rows survive** (the method split, which
  stays county-suppressed, is not emitted as its own rows).

## Name normalization

`norm_name()` normalizes each candidate name alongside the verbatim source (collapses
whitespace, strips the `(NP)`/`(NON)` non-partisan tag). To join elections ↔ votes, further
strip case/suffixes — **election names are UPPER-CASE**; council `all_votes.csv` names are
mixed-case. Alta is at-large, so the join key is **person + year** (no district).

## Rebuilding

```
cd election_results && python3 clean_elections.py     # reads the county canonical, writes the 3 CSVs
```
Idempotent — reads `salt_lake_county/elections/slco_municipal_results_long.csv` directly
(filtered in-code to Town-of-Alta; CANYON + `Cumulative` excluded); no per-city slice to
refresh. **The hand-added cancelled-certification rows (e.g. 2025, Res 2025-R-26) are preserved
byte-for-byte across rebuilds** (`_read_cancelled_raw` carries them through). Re-run when a new
cycle posts to the county file. Add the **2025** county cycle here once the county posts its
SOVC (the election was cancelled → the certification rows already stand; see the gap above).

## Gaps / caveats

- **2021 tallies RECOVERED 2026-07-19** — originally privacy-suppressed; the county released each
  precinct's un-suppressed `Total` sub-row, so the numeric votes are now filled from the county's
  own Totals (Byrne 73 / Anctil 59 / M. Bourke 53; Mayor Bourke 85). The In-Person/Vote-By-Mail
  method split remains county-suppressed. Provenance in the `note` column.
- **2025 not yet in the county file** though the election occurred (Heimark won) — pending
  re-pull (TODO).
- **Alta Canyon Rec decoys EXCLUDED** — a different entity; 0 canyon rows.
- **At-large, no districts** — no per-district races ever; join by person + year.
- Cross-checked against outside sources in `../VERIFICATION.md §4/§5`.
</content>
</invoke>


## 2026-07-17 — 2025 cancelled-certification rows (owner-approved convention, hand-edited)
Two rows were hand-appended to `alta_races.csv` for the **2025 election that was CANCELLED**
under **Utah Code § 20A-1-206**. Per **Resolution 2025-R-26** (adopted 2025-09-10; instrument
text verified in `packets/text/1319417_2025-9-10_Town_Council_Meeting_Packet.txt`, adoption
recorded in the 2025-09-10 minutes), John Byrne and Paul Moxley withdrew their declarations,
leaving each office uncontested, so the Town cancelled the election and the candidates who
qualified were **considered elected**:
- **Mayor: Roger Bourke** (row `office=Mayor`).
- **Town Council (2 at-large seats): Carolyn Anctil and Craig Heimark** (one at-large row;
  `winner`=first-listed Anctil, both named in the `note`).

**Cancelled-certification representation** (matches the Magna convention): `winner` carries the
certified name(s); **all vote-count/percentage/turnout columns are BLANK** (no votes cast —
never fabricated); `uncontested=True`; `n_seats`/`n_candidates`/`voting_method` are structural;
the `note` LEADS with the greppable marker `cancelled_certification (Utah Code 20A-1-206;
Res 2025-R-26)`. `source_file` points at the packet file that carries the verified instrument
text. Dated backup: `_backups/2026-07-17-audited-election-rows/alta/`. (This supersedes the
prior "2025 general entirely absent from alta_races.csv" flag in the repo/CF docs.)
