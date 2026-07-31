# SLC Planning Commission — Votes

Motions + roll-call votes extracted from Salt Lake City **Planning Commission** meeting
minutes (2020–2026). Sibling dataset to `../meeting_minutes` (the City Council votes).
The Planning Commission is an appointed advisory/quasi-judicial body: it **forwards
recommendations** to the City Council on legislative land-use matters and makes **final
actions** on quasi-judicial ones (see "Recommendation vs. final action" below).

## Pipeline

```
minutes/<year>/<week-start Mon>/<date>_planning-commission-meeting.md   acquired minutes (145 files)
minutes_index.csv          one row per minutes file (cols below)
extract_votes.py           PURE REGEX: minutes -> votes/<year>/<week>/<date>_...json ; builds all_votes.csv + roster.csv
validate_votes.py          integrity checks (roster, range, tally, JSON<->CSV, coverage)
votes/<year>/<week>/<date>_planning-commission-meeting.json   per-meeting structured votes
all_votes.csv              long format, one row per member-vote (the analysis file)
roster.csv                 reconstructed commissioner roster
```

`extract_votes.py` is **deterministic Python/regex only** — it does NOT import or call
`anthropic` / any LLM / any network API. It mirrors the council extractor
(`../meeting_minutes/extract_votes.py`): read the index, parse each local markdown file,
write one JSON per meeting, then rebuild the long CSV + roster.
Run `python3 extract_votes.py --force` to discard all per-meeting JSONs and rebuild from
scratch; `--build-only` just rebuilds `all_votes.csv` + `roster.csv` from existing JSONs.

`minutes_index.csv` columns (STANDARD schema since 2026-07-02):
`date, year, title, slug, path, source, source_url, format`
— `path` is the **city-root-relative** path to the markdown
(`planning_commission/minutes/...`); `extract_votes.py` resolves it against the city
root, not this folder, and derives the `votes/<year>/<week-monday>/` bucket from the
path layout. The pre-migration index (legacy header with `week_start`/`meeting_date`/
`file`) is frozen verbatim as `minutes_index_legacy.csv`; the reader still tolerates
the legacy header for old checkouts.

## Extraction model (how the regex parser works)
Per meeting the parser produces `{meta, votes:[...]}` entirely from the local markdown:

1. **Attendance** -> `present`/`absent` full names (staff excluded). Two layouts handled:
   the narrative "Present for the Planning Commission meeting were: … . X was excused."
   (slcdocs/laserfiche) and the labeled "Commissioners Present / Commissioners Absent"
   block (slc.gov 2026). Role words become delimiters and wrapped lines are joined so a
   name split across a line break ("Bree\nScheer") survives. A surname->full-name map is
   built per meeting (present outranks absent for shared surnames -> Mike vs McCall
   Christensen disambiguated by who's actually present).
2. **Motion anchors** = every outcome phrase ("the motion passed/passes/failed/carried/
   did not pass", incl. "Result  The motion passed 6-1"). "did not receive a second" is
   excluded. Each anchor closes one motion; the block back to the previous anchor holds
   that motion's mover/seconder/text/votes.
3. **Per-member vote lists** — dispatched by what the block contains:
   - `Commissioner Yes No` + `Name x` table (2024 laserfiche / slc.gov "x"): the Yes/No
     column is lost on conversion, so trust it **only when unanimous** (all listed = Aye);
     non-unanimous -> tally-only (dissenter unknown, never guessed).
   - `Vote: • Yes: … • No: … • Abstain: …` bullets (2025 laserfiche) and the labeled
     `Vote  Yes: …` block (2026 slc.gov): named; surnames mapped to full names. The list
     stops at the next label whether on a new line or inline (some 2025 files put a whole
     meeting on one line).
   - `Full Name  Y/N [note]` table (slc.gov 2024): the Y/N letter is preserved, so it's
     trusted per row (first column = the motion being voted).
   - Narrative "Commissioners A, B, C voted 'Aye'. … D voted 'No'. E abstained."
     (slcdocs): names pulled per vote-word clause (newlines flattened so wrapped name
     lists stay intact); "All commissioners voted 'Aye'" -> all present. A person can't
     land in two categories (dissent > aye > abstain > recuse).
   If no per-member names are found -> **tally-only** (`names_recorded=false`, empty lists),
   tally parsed from the outcome sentence ("9-0", "4 to one", "seven 'yes' … one 'no'",
   "… one abstention"); a bare "passed unanimously" with no count -> yes = #present, no=0.
4. **Classification** from the motion text (region only as fallback) — see next section.

Names are then **canonicalized** in a second pass (deterministic variant folding: typos /
prefixes / nicknames fold, genuinely distinct first names stay apart) so the roster + CSV
use one spelling per commissioner; a bare surname that voted in a meeting whose attendance
missed that person (late arrival / OCR gap) is resolved to a roster full name by surname.

### CARDINAL RULE — never fabricate
Tally-only outcomes ("the motion passed", "passed unanimously", "seven yes votes",
"passed 8-1") with **no per-member name list** are recorded as the tally with
`names_recorded=false` and **empty** aye/nay/abstain/recuse lists. We never guess who
voted which way. Such motions contribute **no member rows** to `all_votes.csv` (which is
strictly one-row-per-member-vote); they live fully in the JSON and are counted in coverage.

## Source formats (varies by source-year — all three handled)
| source-year | format | per-member names? |
|---|---|---|
| slcdocs 2020–2023 | narrative PDF text: *"Commissioners A, B voted 'Aye'. Commissioner C voted 'Nay'. The motion passed 8-1."* — sometimes just *"passed unanimously"* / *"seven yes votes"* | named when enumerated; else tally-only |
| laserfiche 2024 | a `Commissioner Yes No` table that **linearizes to `Surname x`** — the Yes/No **column is lost** on conversion | unanimous => all listed = Aye; **non-unanimous => tally-only** (cannot identify the dissenter) |
| laserfiche/slc.gov 2025–2026 | structured lists: *"Vote: • Yes: Scheer, Barry • No: Barry"* (surnames) | named (surnames mapped to full names via the attendance line) |

Vote-word map: Yes/aye→Aye, No/nay→Nay, abstain→Abstain, recuse→Recuse, absent/excused→Absent.
Names in vote lists are surnames (2024–2026) and are mapped to full names from each file's
"Present for the Planning Commission meeting were: …" attendance line. Two Christensens
(Mike vs McCall) are disambiguated by attendance (the absent one cannot vote).

## Recommendation vs. final action (encoded in `result`, machine-detectable)
`action_class` ∈ {recommendation, final_action, procedural}; `result` carries a **colon**
tally `N:N` (yes:no):

- **recommendation** — keyed off "forward … recommendation to the City Council" /
  "recommend" / "recommends that the city council adopt". These are the legislative
  matters the PC only advises on: **Master Plan Amendment, Zoning Map Amendment, Zoning
  Text Amendment, Street/Alley Closure.**
  `result` = `"Positive recommendation N:N"` or `"Negative recommendation N:N"`.
- **final_action** — the PC decides: **Conditional Use, Design Review, Planned
  Development, Subdivision/Plat, Special Exception.**
  `result` = `"N:N Approved (Final Action)"` or `"N:N Denied (Final Action)"`.
- **procedural** — minutes approval, consent agenda, table/continue, leave of absence,
  officer elections, findings of fact. `result` = `"N:N Pass"` / `"N:N Fail"`.

## JSON schema (per meeting)
```
meta: {date, year, title:"Planning Commission", body:"PlanningCommission", source,
       source_url, minutes_file, present:[full names], absent:[full names]}
votes: [{motion, description, motion_type, action_class, mover, seconder, result,
         tally:{yes,no,abstain,recuse,absent}, names_recorded,
         aye:[], nay:[], abstain:[], recuse:[], absent:[]}]
```
`present`/`absent` exclude staff (Planning Director/Manager/Attorney/Planner/Assistant).

## all_votes.csv
One row per member-vote. Columns:
`date, year, body, title, motion_no, motion, motion_type, action_class, result, mover,
seconder, names_recorded, member, vote, source`
— `body="PlanningCommission"` and `title="Planning Commission"` on every row (matches the
council `all_votes.csv` core column set, plus `body`/`action_class`/`names_recorded`).
Join to the council votes on `member` (council members never appear here — disjoint
people) or to comments on `date`.

## roster.csv
`commissioner, first_seen, last_seen, n_meetings` — built from `meta.present`/`absent`,
deduped, variants folded. `n_meetings` counts meetings present.

### Appointment cross-check (council confirms PC commissioners)
SLC Planning Commissioners are appointed by the Mayor and **confirmed by the City
Council**, so they appear as `motion_type=Appointment/Advice & Consent` rows in
`../meeting_minutes/all_votes.csv` (e.g. "reappointment of Amy Barry to Planning
Commission", 2022-05-17; "Brian Scott", 2023-12-12). The roster is cross-checked against
those rows — matches are expected for commissioners seated 2021+; pre-2021 seatings
predate the council vote coverage floor and won't have a confirmation row.

## Validation (`validate_votes.py`)
Hard checks (must be 0): off-roster members, out-of-range dates (<2020 or future),
JSON↔CSV row reconcile. Soft (flagged, never auto-fixed): tally mismatches. Also reports
named vs tally-only share by source-year.

## Defaults chosen (no questions asked)
- Consent-agenda approval is ONE procedural vote, not exploded per item.
- Combined motions (e.g. Master Plan + Zoning Map) get the dominant `motion_type`; the
  rest noted in `description`.
- 2024 (and slc.gov "x") non-unanimous table votes → tally-only (column loss on
  conversion; never guess the dissenter). Unanimous "x" tables → all listed = Aye.
- `result` uses colon tallies (`8:1`); council uses dashes (`8-1`) — intentional, so
  recommendation/final-action encoding stays unambiguous.
- **recommendation direction** is computed from the motion's action + outcome:
  approve-and-passed or deny-and-failed → `Positive`; deny-and-passed or approve-and-failed
  → `Negative`. Same logic drives final-action `Approved`/`Denied`.
- A real `recommendation` requires forwarding to the **City Council** ("forward a
  recommendation", "recommend(ation) … city council"); "as recommended by staff" does NOT
  count (that accompanies a final action).
- "passed unanimously" with no numeric tally → tally `yes = #present, no = 0` (the count is
  factual; still `names_recorded=false`, so it contributes no member rows).
- Names that vote but are missing from a meeting's opening attendance (late arrivals) are
  kept faithfully — so a motion's voter count can legitimately exceed `len(present)`.

## Don't
- Don't guess dissenters in 2024 tables or names in tally-only narratives.
- Don't hand-edit `all_votes.csv` / `roster.csv` — rebuild: `python3 extract_votes.py --build-only`.
