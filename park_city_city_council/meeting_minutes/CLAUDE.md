# meeting_minutes/ — Park City Council vote extraction

Turns 238 minutes markdown (2020–2026, CivicClerk) into structured roll-call votes.
Entry point: **`extract_votes.py`**.

## Format (`AYES:/NAYS:` roll call)
```
Council Member Parigian moved to continue Ordinance No. 2024-09 … Council Member Rubell seconded.
AYES:  Council Members Ciraco, Parigian, and Rubell
NAYS:  Council Members Dickey and Toly
```
Also "approved unanimously" (tally-only → `names_recorded:false`, no guessed members), and
`EXCUSED:`/`ABSENT:`/`ABSTAIN:` lines.

## Key handling
- AYES/NAYS/etc. lists captured **across line wraps** (`[\s\S]`) and **comma- AND "and"-separated**
  ("Ciraco, Parigian, and Rubell" → 3). "Council Member(s)" prefix stripped.
- **Mayor does NOT vote except tie-breaks** — excluded from routine rows; **both** tie-breaks in the
  record are captured + labeled `"Nay (Mayor tie-break)"`: Beerman 2020-06-25 (Ord 2020-31 Huntsman
  Estates plat, 2-3 Fail) and Worel 2024-08-22 (Res 16-2024, 2-3 Fail). Councilmembers-turned-mayor
  (Worel mayor 2022–25, Dickey mayor 2026) vote only in their council years.
- **`body`** (`Council`/`RDA`/`HA`): in-council recess detection — "convene as the Redevelopment
  Agency" → `RDA`; "Housing Authority" → `HA`; until "reconvene… City Council" (mirrors Provo).

## Coverage (verified; re-extracted 2026-07-02)
- **238 meetings · 1,557 motions · 7,753 rows · 98 contested · 2020–2026.**
- Body (motions): Council 1,493 · RDA 46 · HA 18. Mayor-roster clean (2 labeled tie-breaks only:
  Beerman 2020-06-25, Worel 2024-08-22). See `../VERIFICATION.md`.

## Repairs (2026-07-02)
- `RESULT_RE`/`LABEL_RE` made **case-sensitive** (all 1,524 genuine CivicClerk result blocks are
  UPPERCASE). The old case-insensitive match created **10 spurious motions** from lowercase prose —
  e.g. a public comment wrapping onto `result: https://www.orlando.gov/...` (2020-06-25), a sentence
  wrapping onto `excused.` (2023-03-02), and title-case "Excused" status cells in roll-call attendance
  tables. Every removed motion was individually verified as non-motion text before re-extraction
  (1,567 → 1,557). One false `Recuse` row (a commenter's *opinion* that Rubell should recuse,
  2022-12-08) was removed with them.
- Note: the source minutes contain **9 clerk errors** where a member appears in both the AYES and
  the NAYS/ABSTAIN list of the same motion (e.g. 2022-10-06 motion 8: "5-2 Pass" on a 5-member
  council). `all_votes.csv` keeps both rows **verbatim** (city-faithful); the documented resolutions
  live in `../db/vote_overrides.csv` and are applied only in the relational db.
- Originals: `_backups/2026-07-02/park_city_city_council/meeting_minutes/`.
