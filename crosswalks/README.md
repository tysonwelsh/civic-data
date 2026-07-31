# Cross-city normalization layer (votes)

**Everything here is derived and regenerable. No canonical file is ever modified.**
City-native values (`motion_type`, `result`, `body`, `vote`) stay verbatim in the
canonical `all_votes.csv` files; this layer sits alongside them.

Regenerate everything (idempotent, stdlib-only, deterministic):

```
python3 scripts/normalize_motions.py --all      # all cities in the registry + these crosswalks (--all required to sweep)
python3 scripts/normalize_motions.py nephi      # one city's motions_std.csv only
python3 scripts/normalize_motions.py --report   # + distribution / cross-check tables
```

The normative contract is `SCHEMA_SPEC.md` §8; `scripts/validate_city.py` checks
conformance (all 26 files pass as of 2026-07-02).

## Files

| file | contents |
|---|---|
| `<city>_city_council/<dataset>/motions_std.csv` | one row per motion (23,110 across 26 files): parsed outcome/tallies/vote_mode + uniform `motion_type_std` / `land_use_type` / `action_class`, joinable to `all_votes.csv` on `(source, motion_no)` |
| `crosswalks/motion_type_crosswalk.csv` | every distinct (city, native motion_type) pair observed in the repo (197 pairs) → `motion_type_std` (+ `land_use_type` where the native label is land-use-specific). Blank std = the native label is genuinely uninformative (`Other`, `Planning Item`, empty) and the text classifier decides |
| `crosswalks/body_crosswalk.csv` | body codes per city → canonical names (RDA=Redevelopment Agency; SLC/nephi CRA=**Community Reinvestment Agency**; MBA=Municipal Building Authority except **lehi, whose docs name its separately-meeting body the Local Building Authority**; LBA; park_city HA=Housing Authority; orem SSLD=Special Service Lighting District; st_george ArtsCommission (different people!) + Canvass (council as Board of Canvassers); Sandy's 10 Legistar bodies from `db/sandy.db`) |
| `crosswalks/vote_values.csv` | each city's recorded vote-value set and ceilings (orem records Aye/Nay only; Recuse exists in 8 cities; sandy adds `Excused` and db-only `Nonvoting`; park_city's 2 `Nay (Mayor tie-break)` rows carry `vote.note` in its db) |

All three crosswalk CSVs are emitted verbatim from tables embedded in
`scripts/normalize_motions.py` — the script is the single source of truth.

## How classification works

1. **Crosswalk** maps the verbatim native label to a candidate `motion_type_std`
   (+ sub-type when the native label is specific, e.g. ogden PC `Rezone`).
2. **One uniform rule set** (~40 ordered regex rules, identical for all cities,
   each with an id recorded as `classify_method=rule:<id>`) runs on the motion text.
   Rules *refine* coarse crosswalk values (native `Land-Use/Zoning` → Rezone vs
   Subdivision-Plat; native `Ordinance` whose text says "zone change" →
   Land-Use/Rezone). On a **top-level** disagreement, rules win only with a
   high-confidence pattern; otherwise the crosswalk value is kept at
   `classify_confidence=medium`. No signal at all → `Other` + `low`, never guessed.
3. **action_class**: SLC PC's own audited `action_class` column is mapped through
   verbatim (`final_action`→`final-action`). Everywhere else: result-string taxonomy
   (`Positive/Negative recommendation` → recommendation; `(Final Action)` →
   final-action) → continuance/tabling phrasing → procedural std categories →
   motion phrasing ("forward a recommendation") → statutory PC default
   (rezone/text/GPA/annexation = advisory) → final-action.
4. **Result parser**: one shared cascade over all 378 distinct result strings
   (8–119 per city file) + a 6-entry exceptions table for true one-offs (nephi's
   named-opposition strings, ogden `Recorded`, sandy bare `Voice`). Outcome is the
   **motion's** outcome: explicit Fail/FAILED words → fail; explicit Pass/Carried →
   pass (even source quirks like logan's `2-3 Pass` — verbatim wins, cross-check
   flags); else tally majority (so `3:4 Denied (Final Action)` = a failed approval
   motion → fail; `9:1 Denied` = a carried denial motion → pass); ties → fail
   (SLC's `5:5 Approved (Final Action)` verified in minutes as a tied — failed —
   motion **to deny**, leaving the CUP approved); `no second` → died. Tallies come
   only from the result string or counted named member rows (with a consistency
   guard for dissent-only rosters), never inferred.

## Verification results (2026-07-02)

- **Hand-verified sample**: 390 motions read across three iterate-and-fix rounds
  (stratified ≥10/city, both datasets, all confidence levels; final fresh 130-motion
  sample after the last rule fix: **128/130 correct (98.5%)**. The 2 residual errors:
  an orem ordinance amending "Standard Land Use Code" tables kept as `Ordinance`
  (no uniform text signal distinguishes it from non-zoning city-code amendments),
  and a park_city continuance of a "Condition Use Permit" (source typo for
  Conditional) kept as `Procedural-Administrative`. Both are `medium` confidence.
  Earlier rounds' systematic errors (compound "close hearing and adopt X" motions,
  `CONTINUED` phrasing, rezone-with-development-agreement precedence, provo `PL***`
  petition prefixes, park_city "Land Management Code") were fixed in the rules and
  re-run — every fix verified against the same motions.
- **Outcome coverage** (`outcome != unknown`): 100.0% in 24 of 26 files;
  **ogden meeting_minutes 91.6%** (126 `Recorded` motions — the extractor's fallback
  where the narrative's outcome words were OCR-garbled, e.g. "ALL VOTING A YE", and
  no names were printed; honest unknowns) and sandy meeting_minutes 99.5%
  (4 bare `Voice` motions whose outcome the minutes never state).
  Repo-wide: 22,980/23,110 = **99.4%**.
- **Tally cross-check** (parsed result tally vs counted named member rows, 17,854
  motions with both): 100.0% in 9 cities; logan 99.9% (1), vineyard 99.5% (2),
  sandy 98.5% (16), provo 90.4% (102), west_jordan 82.0% (209). Every disagreement
  class was inspected: provo, sandy(2020-era) and west_jordan-PC minutes name **only
  dissenters/absentees**, so counted Ayes < stated tally by design (west_jordan PC's
  named rows are exclusively Absent/Nay/Abstain). These are documented source styles,
  not extraction errors; `tally_*` always prefers the stated string.

## Distribution sanity (motion_type_std share per city, % of motions)

```
category                      lehi   logan   nephi   ogden    orem park_ci   provo   sandy     slc st_geor vineyar west_jo west_va
Land-Use                      65.1    26.7    20.6    13.4    34.2    32.6    39.3    40.9    26.0    55.5     9.4    23.8    35.0
Ordinance                      1.6     8.9     5.5    11.0     4.9     3.4    12.9     4.8     6.2     4.3     5.2    13.4     5.1
Resolution                     9.2    18.6     4.1     7.8     4.3     5.5    17.3     9.7     4.9     2.0     5.7    13.6    14.4
Budget                         1.5     4.9     1.0     5.5     2.5     1.9     5.2     2.6     5.8     1.8     2.7     8.5     2.6
Appointment                    2.2     7.5     2.3     6.3     5.1     3.9     9.5     4.4     2.1     3.0     5.1     7.8     1.0
Contract-Purchase              3.4     0.0    12.4     0.5     1.1     7.4     2.0     0.7     0.6     1.7     2.5     1.0     6.1
Grant-Funding                  0.5     0.0     0.5     0.3     1.8     0.2     1.1     0.5     1.4     0.9     0.3     1.5     2.0
Interlocal                     1.1     0.1     0.3     0.7     0.2     0.4     2.0     1.3     1.4     1.3     0.6     1.2     0.9
Ceremonial                     0.1     0.1     1.0     2.1     0.2     0.2     0.0     0.2     3.0     0.1     0.4     0.0     0.0
Procedural-Administrative     11.1    29.5    37.4    30.8    43.6    38.6     2.6    24.9    31.3    26.8    30.8    24.6    32.1
Public-Hearing                 2.9     0.0     1.5    17.5     0.3     0.6     0.3     0.7    13.4     0.0    26.7     1.2     0.1
Legislative-Intent             0.0     0.0     0.0     0.0     0.0     0.0     0.0     0.0     1.0     0.0     0.0     0.0     0.0
Other                          1.2     3.8    13.5     4.0     1.9     5.4     7.7     9.2     2.9     2.6    10.5     3.3     0.8
```

Residual gaps that are **real, explained differences** (not classifier skew):

- **ogden Land-Use 13.4%** (was 9.3%; council 1.5% → 6.9%, PC 38.1% unchanged): the
  honest residual from 2.3 — ~500 bare adoption formulas ("ORDINANCE WAS PASSED AND
  ADOPTED AS OGDEN CITY ORDINANCE 20xx-N…") whose subject lived only in un-captured
  agenda headings — was **fixed 2026-07-02 (plan item 3.5)**: ogden's extractor now
  appends the item's verbatim statutory long-title (`[ENTITLED: "An ordinance …"]`,
  488 motions) or agenda heading (`[AGENDA ITEM: "…"]`, 12) to the motion text,
  matched by ordinance/resolution number (nearest-preceding introduction for the
  no-number resolution form); all 500 verified verbatim substrings of their minutes.
  208 of the 500 reclassify (74→Land-Use incl. 52 rezones, 96→Budget, 14→Interlocal,
  …); 284 legitimately remain Ordinance/Resolution (their long titles are non-land-use
  code/fee amendments — real, not classifier skew). 1 motion stays unenriched:
  2025-08-19 prints "ORDINANCE 2025-23 WAS ADOPTED" but the meeting introduced only
  2025-26 — a source number mismatch we do not guess across. Ogden's remaining gap vs
  lehi is the real routing difference plus its 2022–23 RDA/MBA coverage gap. Details:
  ogden VERIFICATION.md (2026-07-02 Phase 3.5 addendum).
- **lehi 65.1% vs logan 26.7% Land-Use**: real. Logan's PC takes *final action* on
  most land use (`Approved (Final Action)` results), so its council sees little of
  it (6.5%); Lehi routes everything through council and is a high-growth city.
- **vineyard Public-Hearing 26.7% / slc 13.4% / ogden 17.5% vs st_george 0.0%**:
  a *recording* difference — vineyard/slc/ogden minutes record every open/close-
  hearing motion as its own vote; st_george's extractor captured none. Vineyard's
  low Land-Use share (9.4%) is the flip side of the same coin plus its many
  procedural motions.
- **provo Procedural 2.6%**: provo's extraction is item-level (work-session straw
  polls, "A discussion regarding…"), and minutes approvals ride consent items that
  weren't separately extracted. Source-faithful.
- **nephi Other 13.5%**: nephi's motion texts are frequently truncated mid-word by
  its extractor ("approve th", "accept the results a") — no signal, honest
  `Other`/`low` (a known nephi extraction limitation, see its VERIFICATION.md).

## Per-city caveats

- **sandy PC**: `source` is a constant Legistar-staging string, so join on
  `(source, motion_no, date)` (the validator WARNs on the degeneracy by design).
  Its items are titles, not motion phrasing; where the title carries no signal the
  motion stays `Other`/`low` (73 motions). Its `action_class` for land-use items
  falls back to the statutory rule (rezone/text/GPA/annexation → recommendation).
- **ogden mm**: 126 `outcome=unknown` (see above) — the only city below the 97%
  coverage target; 2 further `Recorded` motions recovered as `died` from
  motion-text "died for lack of a second".
- **west_jordan `''` results** (3 motions): outcome taken from the full named roll
  call (`members-majority`), tallies counted from rows.
- **west_valley `4-2 Unanimous Pass`**: documented source quirk — tally parsed as
  4-2, outcome pass, verbatim string preserved.
- **park_city**: `5-0 September 17, 2020 Minutes Approved`-style leaks parse as
  tally 5-0 + pass via the generic tally/action-word rules; the two mayoral
  tie-break Nays live in `vote` (CSV) and `vote.note` (db).
- **nephi**: `4-0 Pass (1 recused)` → `tally_other=1`; named-opposition strings
  (`Pass (Ann Peterson, Cory Thomson opposed)`) are table-driven exceptions
  (nay counted from the names, aye left blank).
- **logan `2-3 Pass`** (5 rows ≈ 1 motion) and similar stated-outcome-vs-tally
  contradictions: the verbatim outcome word wins; the cross-check reports them.
- **Absent/Excused are never counted into `tally_other`** — only recorded non-aye/nay
  *votes* (Abstain, Recuse). `vote_mode=roll-call` means ≥1 named member row exists;
  in provo/sandy(2020)/west_jordan-PC that roster may cover dissenters/absentees only.
- **SLC PC** keeps its own audited `action_class` verbatim; its native label variants
  (`Contract/Property`, `Appointment/Advice & Consent`, `Ceremonial Resolution`,
  `Grant/Funding`, `Interlocal/Agreement`, `Legislative Intent`) are crosswalked, and
  `Legislative-Intent` is (correctly) SLC-only in the whole repo.
