# salt_lake_county / land_use — Planning Commission votes

Roll-call / motion votes extracted from the 97 County Planning Commission minutes in
`minutes/**/*.md` (both bodies). Companion to this module's minutes text corpus — see
`CLAUDE.md` and `SOURCES.md` for the minutes provenance.

## Recording ceiling (READ THIS FIRST) — affirmatives are tally-only

These minutes record every motion in a fixed four-field block:

```
Motion: <subject / full motion text>
Motion by: Commissioner <surname>
2nd by:    Commissioner <surname>
Vote:      Commissioners voted unanimous in favor (of commissioners present)
```

The **`Vote:` line names NO individual affirmative voters.** The outcome is written as a
tally — "Commissioners voted unanimous in favor (of commissioners present)". The only
individuals ever named on a vote are **dissenters and abstainers**, e.g.:

- `Commissioner Omer voted nay, all other Commissioners voted in favor …`
- `Commissioners Omer, Reid, and Jones abstained. All other commissioners voted in favor …`

So the recording ceiling is: **movers and seconders are named for (nearly) every motion;
Ayes are never individually named; only Nay/Abstain dissenters are named.** This is the
same ceiling as the repo's West Jordan PC and South Jordan PC bodies. Consequently the
per-member vote file (`all_votes.csv`) contains **only the named Nay/Abstain rows** — there
are **zero named-Aye rows**, by source design, not by extraction failure.

Additional ceiling facts, measured across all 97 files:
- **No numeric tallies** ("5-0", "4 to 1") appear anywhere — outcomes are prose only.
- **Every recorded motion carried** (all `Vote:` lines are "unanimous in favor" or a named
  dissent with "all other … voted in favor"). No failed/denied/tabled-by-vote motions were
  found in the minutes text.
- **Recusals appear only in narrative prose** ("Commissioner Cole recused himself from this
  application …", 10 statements) and are **never** part of a `Vote:` line. They are not
  attributed to specific `motion_no`s here (the prose→motion linkage is ambiguous) — a
  documented gap, not a fabricated row.

## Files produced

| File | What it is |
|---|---|
| `all_votes.csv` | Standard 13-column vote file. **One row per NAMED member-vote** (Nay/Abstain only, per the ceiling). 16 rows / 13 motions. |
| `motions_tally.csv` | The 297 motions with **no named member** (tally-only outcomes). Columns: `date,body,motion_no,motion,result,mover,seconder,names_recorded` (`names_recorded=false` for all). Keeps the motion on record even though no member vote can be attributed. |
| `roster.csv` | `commissioner,first_seen,last_seen,n_votes`. Built from every named participant (mover / seconder / named-voter). `n_votes` = count of motions in which that commissioner is named in any of those roles (NOT an Aye count — Ayes are unrecorded). |

`all_votes.csv` columns (identical to every other body in the repo):
`date,year,title,body,motion_no,motion,motion_type,result,mover,seconder,member,vote,source`

- `body` = `PlanningCommission` or `MountainousPlanningCommission`; `title` = the full
  body name.
- `motion_no` = per-meeting motion sequence (1, 2, 3 …).
- `motion` = the verbatim motion subject/text; `result` = the verbatim `Vote:` outcome
  string (trailing next-agenda-line bleed trimmed at the outcome boundary).
- `motion_type` is **blank** — these minutes print no native motion-type label distinct
  from the motion text (leaving it blank is honest, per the never-fabricate rule).
- `mover`/`seconder` = surnames as printed (blank where the source left them blank).
- `member`/`vote` = the named dissenter/abstainer and their vote ∈ {Nay, Abstain}.
- `source` = md path relative to `salt_lake_county/`.

## Counts

| Body | Meetings | Motions | Named-vote motions | Named member-rows | Tally-only motions |
|---|---|---|---|---|---|
| Planning Commission | 62 | 203 | 2 | 2 | 201 |
| Mountainous Planning District PC | 35 | 107 | 11 | 14 | 96 |
| **Total** | **97** | **310** | **13** | **16** | **297** |

- **Date range:** 2020-01-02 … 2026-03-19 (every meeting in the minutes corpus produced at
  least one motion).
- All 16 named rows are Nay (5) or Abstain (11). 11 of the 13 named-vote motions are on the
  Mountainous PC (the valley Planning Commission is near-unanimous — only 2 named dissents
  in 203 motions).
- 32 distinct commissioners in `roster.csv`; most-active: Vance (116), Cohen (106),
  Elieson (53), Watkins (53).

## Extraction method

Pure text parsing of the born-digital minutes markdown (`scripts`-free; no network, no
build scripts touched). Per file: parse the YAML front-matter for `body`/`date`; label
each body line as one of `Motion:` / `Motion by:` / `2nd by:` / `Vote:`; group them **in
document order** into motions (this ignores the attendance tables that pypdf interleaves
between the fields in some files). Named voters are extracted **only** from explicit
"Commissioner X voted nay" / "Commissioner(s) X, Y … abstained" clauses on the `Vote:`
line. When a motion is unanimous or names no individual, **no member row is emitted** — the
motion is written to `motions_tally.csv` instead.

## Honest gaps / caveats

- **No named Ayes anywhere** — source ceiling (above). Do not infer who voted yes; the
  attendance tables list who was *present at the meeting*, which is not the same as who
  voted on a given motion.
- **Recusals (10) are prose-only** and unlinked to motion numbers — omitted from member
  rows on purpose.
- **Blank mover/seconder** on some motions (mostly the start-of-meeting minutes-approval
  and officer-election motions) reflect blanks in the source, left empty (not guessed).
- **Verbatim surname spelling variants** in `roster.csv` reflect source typos, kept as-is
  rather than silently merged: `Sorensen`/`Sorenson`, `Paredes`/`Parades`, and `O'Meara`
  (curly apostrophe). Treat these pairs as likely the same person; no canonical merge was
  fabricated.
- **`result` bleed trimming:** a few `Vote:` lines run straight into the next agenda line
  in the pypdf text (no blank between). Results are trimmed at the natural outcome boundary
  ("Motion passed." / "(of commissioners present)" / "voted unanimous in favor"); the full
  motion context remains in the source md.
- This layer covers only what the **minutes** printed. Meetings with no posted minutes,
  cancelled meetings, and pending-approval recent meetings are enumerated in `CLAUDE.md`
  (they are absent here by definition, not extraction failures).
