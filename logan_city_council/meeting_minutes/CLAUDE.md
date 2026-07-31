# meeting_minutes/ — Logan Municipal Council vote extraction

Turns 198 minutes markdown (149 Council + 49 RDA, 2020–2026) into structured roll-call votes.
Entry point: **`extract_votes.py`**.

## Format (per-member roll call)
```
Motion by Councilmember Bradfield seconded by Councilmember M. Bradfield to approve
Resolution 20-04. Motion carried by roll call vote.
   A. Anderson: Aye
   M. Anderson: Aye
   ...
```
Also "Motion carried unanimously" (tally-only → `names_recorded:false`, no guessed members), and
split votes with `Name: Nay/Abstain/Absent`.

## Key handling
- **Page-footer/`DRAFT` lines** that `-layout` interleaves mid-vote-block are filtered so they don't
  break the `Name: Vote` sequence.
- **Two Andersons kept distinct** by initial+surname: `A. Anderson` = **Amy Z. Anderson** (council
  2021); `M. Anderson` = **Mark A. Anderson** (council 2019/2023, Mayor 2026+). Roster built from the
  per-meeting attendee headers + election winners.
- **Mayor does NOT vote** (separately elected, veto) — excluded from vote rows; Mark A. Anderson
  votes 2019–2025 as councilmember but 0 rows in 2026 (mayor).
- **`body`**: slug `city-council-meeting`→`Council`; `redevelopment-agency-meeting`→`RDA` (the
  same-night RDA recess, split into its own file during acquisition).

## Coverage (verified)
- **198 meetings · 789 motions · 2,820 rows · 28 contested · 2020–2026.**
- Body: Council 754 motions / 2,714 rows · RDA 35 / 106. Mayor-roster clean (no leak). See
  `../VERIFICATION.md`.
- **2026-07-20** — +5 council motions recovered via the `ANCHOR3` fix (see extract_votes.py):
  minutes where the clerk dropped the leading "Motion by", leaving `ACTION. <mover> seconded by
  <seconder> to …` (2023-05-02 Ord 23-15 + Res 23-13; 2025-04-01 Res 25-11/25-12/25-13). All 5-0.
- **2026-07-20** — +1 council motion via the `ANCHOR4` fix (see extract_votes.py): the WORD-SCRAMBLED
  adoption form `ACTION. Motion Councilmember A. Anderson by Vice Chair Johnson seconded by to adopt
  Ordinance 25-21 … (4-0)` (2025-12-02, sole corpus instance). Roll call captured verbatim (4-0);
  **mover/seconder left BLANK** — the scramble makes the two names' mover/seconder order genuinely
  ambiguous (position → A. Anderson; the `…by Vice Chair Johnson` preposition → Johnson), so neither
  is guessed.
