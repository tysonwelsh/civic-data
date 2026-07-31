# cache_county / land_use — the vote layer (method + recording ceiling)

`build_votes.py` reads `minutes/**/*.md` and writes `all_votes.csv`,
`motions_tally.csv`, `roster.csv`. DERIVED, idempotent, no network.

## The two grammar eras (the recording ceiling)

Cache County PC minutes state each motion inline in prose. The recording depth **changes
hard at 2024-11-07**:

| Era | Dates | What the source records | Where it lands |
|---|---|---|---|
| **Tally** | 2015-01-08 … 2024-10-03 | `"<Mover> motioned to <text>; <Seconder> seconded; Passed <aye>, <nay>."` — count only; **no voter named, even dissenters on splits** | `motions_tally.csv` (`names_recorded=false`) |
| **Named** | 2024-11-07 → present | same line **plus** `"Ayes: <full names>" / "Nays: <names or 0>"` — every member named, even on unanimous votes | `all_votes.csv` (one row/member) |

A minority of named-era **procedural** motions (open/close public hearing, extend
meeting) print only a tally and stay in `motions_tally.csv`. Honest ceiling variation,
not a miss.

## Files & columns

- `all_votes.csv` — `date, year, title, body, motion_no, motion, motion_type, result,
  mover, seconder, member, vote, source`. `motion_type` is intentionally blank (native
  data only; normalization is downstream). `result` is the verbatim outcome
  (`"Passed 4, 0"`). `member`/`vote` = the named Aye/Nay/Abstain. Named era only.
- `motions_tally.csv` — `date, body, motion_no, motion, result, mover, seconder,
  names_recorded`. Every tally-only motion. `result` is `"Passed <a>, <n>"`, a bare verb
  (`Approved`), or `"Motion died due to lack of a second"` (4 motions that never reached
  a vote — an honest outcome, not a missing tally).
- `roster.csv` — `commissioner, first_seen, last_seen, n_votes` from named roles
  (mover / seconder / named voter). Surnames dominate the tally era; full names appear in
  the named era. OCR variants are present verbatim (see below).

## Extraction notes (why the parser looks the way it does)

- **Anchored per motion.** Each motion is bounded by successive `"<Name> motioned"`
  anchors, so a single regex can never merge two motions when margin line-numbers bleed
  between the seconder clause and the outcome.
- **Margin line-number bleed.** The 2015–2016 (and some 2024) scans carry line numbers
  that pypdf interleaves into tallies: `"Passed 6, 35 \n0."`, `"Passed 28 6, 0"`,
  `"Passed 9 5, 0"` all mean the printed tally with the stray line-number removed. The
  result regex tolerates a leading junk number and takes the nay as the digit group
  before the terminating period. Verified: all extracted nay counts are 0 (809), 1 (34),
  or 2 (4) — no line-number artifacts survive.
- **Format variants handled:** comma OR hyphen tally (`6, 0` / `6-0`), lowercase verb
  (`passed 5, 0`), comma after verb (`Passed, 5, 0`), verb-dropped bare tally
  (`seconded; 7, 0.`), and `"Motion die(s/d)/withdrawn"` non-outcomes.
- **`(check)`** editorial QA markers are stripped so they never surface as a name; a
  literal `"Check seconded"` (a clerk placeholder in the 2024-10-03 source) is kept
  **verbatim** per the never-overwrite rule.

## Ground-truth

Extraction was sample-verified against the source PDFs across the full date range and
both eras; the motion count (1,025) equals the count of `"<Name> motioned"` occurrences
in the corpus (zero dropped/merged motions). **OCR name variants** (e.g. `Nate Dauges`
↔ `Nate Daugs`, `Christesen`/`Chirstensen` ↔ `Christensen`, `Waterson` ↔ `Watterson`,
`Riby`/`Rigyb` ↔ `Rigby`) appear as low-count roster rows — verbatim reflections of the
source text, deliberately not normalized here (that belongs to a downstream crosswalk).
