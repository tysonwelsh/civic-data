# Lehi City Council — vote-extraction pipeline

This directory turns the Lehi council/board **minutes markdown** into structured
roll-call vote data: one JSON per meeting plus a flat `all_votes.csv`.

## Files
- `minutes_index.csv` — 175 meetings, 2020–2026 (`date,year,title,slug,path,source,source_url,format`).
  (2026-07-02: 6 duplicate same-date Granicus events removed — one minutes doc had been attached to
  two consecutive clip_ids; verified md5-identical at source. See ../VERIFICATION.md addendum.)
- `minutes/<year>/<week>/<date>_<slug>.md` — the source minutes (Granicus text layer).
- `extract_votes.py` — parses each meeting → `votes/<year>/<week>/<date>_<slug>.json`,
  then rebuilds `all_votes.csv`. Resumable (skips meetings whose JSON exists); `--force`
  re-extracts all.
- `validate_votes.py` — reads the JSONs → `votes/_validation_report.txt`.
- `all_votes.csv` — long format, **one row per member-vote**:
  `date,year,title,body,motion_no,motion,motion_type,result,mover,seconder,member,vote,source`.

## Run
```bash
python3 meeting_minutes/extract_votes.py --force
python3 meeting_minutes/validate_votes.py
```

## Roster (built from the corpus, 2020–2026)
Five at-large seats; staggered terms. Surname → canonical name:

| held the seat across the window | current cohort (2025+) |
|---|---|
| Paige Albrecht, Chris Condie, Paul Hancock, Katie Koivisto, Mike Southwick | Rachel Freeman, James Harrison, Emily Lockhart |
| Heather Newall, Michelle Stallings (carry forward) | |

OCR/typo variants are normalized (`Codie→Condie`, `Hanock→Hancock`, `Newell/Newal→Newall`,
`Stalling→Stallings`, `Koiviso→Koivisto`, `Albreht→Albrecht`). Staff/residents named in the
narrative are dropped — only roster surnames map to a vote.

### The Mayor is NON-VOTING
Mayor **Mark Johnson** (2020–2025) and Mayor **Paul Binns** (current) **preside and do not
vote**, so they are kept OUT of the voting roster. They are emitted **only** when the
minutes explicitly record a tie-break vote — captured two ways:
1. inline pair: `…Mayor Johnson, No.`
2. narrative: `Mayor Johnson voted YES.` / `Mayor Jonson was asked to break the tie and
   voted Yes.` (note the `Jonson` typo is mapped).

When the Mayor breaks a tie his vote is folded into the aye/nay tally (so the result
reflects reality, e.g. a 2:2 council split that the Mayor resolves to `3:2 Pass`) and the
vote record is flagged `mayor_tiebreak:true`. There are **4** such votes in the corpus
(2022-06-14, 2023-04-11, 2024-03-26, 2025-12-16). `validate_votes.py` confirms the Mayor is
NOT a routine voter — he appears in the per-year roster only on those 4 rows.
**`Mayor Pro Tempore <Surname>`** is a *councilor* acting as chair → mapped to that
councilor, never to the Mayor.

## Roll-call formats (both handled)
**Format A — per-member inline** (most common):
```
Roll Call Vote: Councilor Albrecht, Yes; Councilor Condie, No; Councilor Hancock,
Absent; Councilor Newall, Yes; and Councilor Stallings, Yes. The motion passed with
3 in favor, 1 opposed, and 1 absent.
```
**Format B — label blocks** (2025+ and some earlier):
```
Roll Call Vote:   YES: Paige Albrecht, Chris Condie, Paul Hancock, Heather Newall,
                  Michelle Stallings.   NO: None. The motion carried: 4 - 0
```
The MBA meetings use `Vote:` (not `Roll Call Vote:`) and `Mr./Ms. <Surname>` prefixes.
Maps: Yes/Aye→aye, No/Nay→nay, Absent/Excused→absent, Abstain→abstain, Recuse→recuse.

The whole vote block is **flattened** (line wraps joined) before parsing, because the name
lists wrap onto the next line. Names are anchored on **roster surnames**, so they parse
regardless of whether the separator is a comma, a semicolon, or "and". The result clause
(`The motion passed/failed/carried…`) is sometimes set off by a **blank line** from the
roll call — the parser peeks past the blank for that one clause so the outcome and any
narrative Mayor tie-break are not lost.

`result` is the literal tally + outcome (`3:1 Pass`, `2:3 Fail`, `5:0 Pass`,
`Unanimous Pass`), oriented by the pass/fail verb; counts come from the named roll call.
When a motion gives only a tally with no per-member names we set `names_recorded:false` and
emit **no** member rows — we never guess who voted which way.

## `body` column — Council / RDA / MBA
- Slug `building-authority-meeting` → **MBA** (the 9 standalone Local Building Authority
  meetings; 8 of them recorded a roll-call vote, two are bare adjournments with no roll
  call). Slug `city-council-meeting` → default **Council**.
- **In-council RDA recess**: the parser runs a state machine for a *matched* open→close
  bracket — a line that "recesses / adjourns / moves into the Redevelopment Agency" OPENS
  an RDA bracket and the next "reconvened" line CLOSES it; motions inside are tagged `RDA`
  (MBA likewise for a Building-Authority recess). A line that contains the word "motion"
  (the motion *to* recess) does not open a bracket — that vote is Council business.
- **Reality for Lehi (honest gap):** Lehi minutes its RDA business in a **separate record**.
  In the council files the RDA recess and the reconvene are back-to-back (e.g. "recessed at
  8:00 p.m. / reconvened at 8:05 p.m.") with **no motions between them**, so `body=RDA`
  resolves to **0** in-council motions — that is expected, not a miss. An **unmatched** open
  (a "recess for an RDA meeting" with no reconvene before adjournment) is **discarded**, not
  left open, so the council items that follow are correctly tagged `Council` rather than
  swept into a runaway RDA bracket.

## Motion-type taxonomy (fixed 12 categories)
`Ordinance, Resolution, Budget Amendment, Grant-Funding, Interlocal, Appointment,
Public Hearing Action, Procedural/Administrative, Ceremonial, Contract/Purchase,
Land-Use/Zoning, Other`. Land-use is checked first (most are technically ordinances).
A procedural **sub-motion** (recess / move into a board meeting / closed session / table /
adjourn) is described and classified from the **motion text**, not the substantive agenda
item it happens to sit under.

## Validation (`votes/_validation_report.txt`)
Reports motion + body counts, motion-type distribution, the per-year observed-voter roster
(with the Mayor flagged as tie-break-only), Mayor tie-break list, **tally-vs-result
mismatches** (named count vs the minutes' own printed tally), outcome-vs-count
inconsistencies, roster-size deviations, and the full contested-vote list.

- **Tally-vs-result mismatches are NOT auto-corrected.** The two current mismatches
  (2023-01-24 m3, 2025-03-18 m13) are **source typos**: the minutes' printed summary
  ("4 in favor") contradicts its own named roll call, which clearly lists one dissenter.
  The verbatim names are authoritative; the mismatch is logged for the record.
- **Roster-size deviations** (123) are motions where fewer/more than 5 members are recorded:
  almost all are a single absent member who was simply omitted from the roll call (4 names),
  the late-2025 council **vacancy** after Albrecht's resignation (4 seats), or a Mayor
  tie-break (6 = 5 councilors + Mayor). All reviewed; none are parse errors.

## Current corpus stats
175 meetings · 1253 motions · 6147 member-vote rows · body {Council 1245, RDA 0, MBA 8} ·
99 contested · 4 Mayor tie-breaks · 2 (source-typo) tally mismatches · 0 outcome issues.

## Known gaps (honest)
- Bare inline procedural motions with **no roll-call label** (e.g. "moved to adjourn the
  meeting. The motion passed unanimously.") are not captured — the parser anchors on
  `Vote:` / `Roll Call Vote:` labels. These are the lowest-signal procedural votes.
- In-council RDA/MBA business is not in these files (minuted separately), so `body=RDA`=0
  is by design — Council-only analysis = filter `body=Council`.
