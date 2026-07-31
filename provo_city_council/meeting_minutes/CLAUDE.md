# meeting_minutes/ — Provo Municipal Council vote extraction

Pipeline that turns 311 council-minutes markdown files into structured roll-call
vote data. Entry point: **`extract_votes.py`**.

## What's here

| Path | Role |
|------|------|
| `minutes/<year>/<week-monday>/<date>_<slug>.md` | Source minutes (born-digital PDF → markdown). Immutable input. |
| `minutes_index.csv` | Index of the 311 files (`date,year,title,slug,path,source,source_url,format,packet_url`). One file is `format=pdf-ocr` (lower fidelity). |
| `extract_votes.py` | Parser. Reads each minutes file, emits one JSON per meeting, rebuilds `all_votes.csv`, writes the validation report. |
| `votes/<year>/<week>/<date>_<slug>.json` | Structured intermediate, one per meeting (schema below). |
| `votes/_validation_report.txt` | Per-member-count vs tally cross-check; lists every mismatch with an explanation header. |
| `all_votes.csv` | Long format, one row per member-vote, rebuilt from the JSONs. Authoritative analysis table. |

## Run

```bash
python3 meeting_minutes/extract_votes.py          # resumable: skips meetings whose JSON exists
python3 meeting_minutes/extract_votes.py --force   # re-extract every meeting
```

The CSV and validation report are always rebuilt from **all** JSONs on disk, so a
resumed run still produces a complete `all_votes.csv`.

## Schemas

Per-meeting JSON:
```json
{"date":"2024-03-05","title":"Council Regular Meeting",
 "source":"meeting_minutes/minutes/2024/2024-03-04/2024-03-05_council-regular-meeting.md",
 "format":"pdf",
 "votes":[{"motion_no":1,"motion":"An ordinance vacating ...","body":"Council",
           "motion_type":"Land-Use/Zoning",
           "result":"6:0 Pass","mover":null,"seconder":null,
           "aye":["Becky Bogdin","..."],"nay":[],"abstain":[],"absent":["Rachel Whipple"],
           "recuse":[],"names_recorded":true}]}
```

`all_votes.csv`: `date,year,title,body,motion_no,motion,motion_type,result,mover,seconder,member,vote,source`
— one row per (motion × member). `vote` ∈ {Aye, Nay, Abstain, Absent, Recuse}. A
tally-only motion (`names_recorded:false`) emits **one** row with empty `member`/`vote`
so the motion is still represented. `body` is also written into each per-meeting JSON
(on every vote record, after `motion`).

### `body` column — governing body that took the vote
`body` ∈ {`Council` (default), `RDA`, `CRA`, `MBA`}. In Provo the Municipal Council does NOT
hold separate RDA meetings — it **recesses mid-meeting and "convenes as the Governing Board of
the Redevelopment Agency"**, votes on tax-increment / project-area / RDA-budget items (same 7
people, board capacity), then "reconvenes as the Municipal Council". Those board-capacity
motions are tagged `body=RDA`; everything else is `body=Council`. **These are NOT new rows** —
the RDA motions always lived inside the `Council Regular Meeting` minutes and were previously
all mislabeled `Council`; this is a re-tag in place. Filter `body=Council` for council-only
analysis; `body=RDA` is the "follow the money" RDA subset.

How `body` is assigned (`detect_body_for_line` + `resolve_motion_body`):
1. **Transition markers.** Each line is scanned for a body transition — a *transition verb*
   (`convened`/`reconvened`/`recessed`/`adjourned`) **plus** a body keyword. The DESTINATION
   body (read from the text after the last "as the …" cue) sets the segment body for all
   following motions. Provo's phrasing is highly variable ("recessed and convened as the
   governing board of the Redevelopment Agency", "With no objections, the Provo Municipal
   Council adjourned and reconvened as the Redevelopment Agency of Provo", "Chair X convened
   the Redevelopment Agency", "reconvened as the Municipal Council", …) and these sentences
   often **wrap across 1–2 lines**, so detection tests each line joined with the next two.
2. **Per-motion override.** Provo frequently OMITS the "reconvened as the Council" marker, so a
   segment can run on into council business. Each motion is re-checked against its own
   Motion/Vote text: a body-prefixed item id (`2025-RDA-03-11-1`, `…-CRA-…`, `…-MBA-…`) pins
   the body unambiguously; board-role names ("Board Member"/"Agency Member") confirm a board
   **only when a redevelopment segment marker corroborates** (the **Board of Canvassers** ALSO
   seats "Board Members" + Mayor Kaufusi and is NOT the RDA — so a bare board-role name never
   creates RDA on its own); explicit "Councilor" naming pins a motion back to `Council`,
   overriding a stale RDA segment left open by a missing reconvene marker.
3. **Role-name synonyms map to the SAME people.** "Board Member Handley" / "Chair Ellsworth" in
   board capacity resolve to the same `ROSTER` member names as "Councilor Handley" — no new
   members are created. (Verified: the set of RDA voters is a strict subset of the council
   voters; zero RDA-only members.)
4. **Out of scope: Stormwater Service District (SSD).** Provo also "convenes as the Governing
   Board of the Provo City Stormwater Service District". SSD is a real separate body but is NOT
   one of the RDA/CRA/MBA financing bodies the schema models, so SSD blocks fall back to the
   default `body=Council` (and are noted here). `CRA`/`MBA` are supported in code but **0** in
   the current corpus — "Community Reinvestment" appears only as RDA *project-area* names
   (subject matter), never as a body the council convenes as; no Municipal Building Authority
   blocks exist.

**Counts (current run):** `Council` = 5968 rows / 1015 motions · `RDA` = 404 rows / 59 motions
across **39** meetings (all titled `Council Regular Meeting`) · `CRA` = 0 · `MBA` = 0.
Contested motions (≥1 Nay/Abstain/Recuse) split: **Council 158, RDA 4**. Every RDA motion is
corroborated by an RDA-prefixed item id and/or a redevelopment transition marker in its source
file (0 over-tags); 0 under-tags (every meeting with "Board Member" votes inside a redevelopment
block has ≥1 RDA motion). RDA voters: Bogdin, Fillmore, Christensen, Harding, Sewell, Shipley,
Garrett, Handley, Whitlock, MacKay, Whipple, Ellsworth, Hoban — all on the council roster.

### Acquisition gap — separate standalone RDA meetings (NOT re-acquired)
The recon scrape enumerated only the **Council Work/Regular** meeting types in Provo's OnBase
portal (`agendas.provo.gov`); the portal also exposes a separate **"Redevelopment Agency" board
meeting type** (recon.md §"Meeting bodies") that was **filtered out at scrape**. In practice
Provo conducts essentially all RDA action *inside* council regular meetings (every RDA vote we
found is an in-council board block — there are **0 RDA-titled minutes docs on disk**), so the
core RDA voting record is captured by the in-place re-tag above. Whether Provo *also* holds any
RDA-only sessions with no concurrent council meeting (distinct minutes PDFs) **cannot be
enumerated from disk** and was not probed (text-only, no-download task). Count of separate RDA
minutes docs confirmed missing on disk: **0 located**; the OnBase "Redevelopment Agency" meeting
type remains **un-enumerated** and is flagged for a bounded re-acquisition probe in a later pass
(do NOT re-acquire now).

## How Provo minutes encode votes

Each recorded motion is a `Motion:` block followed (after discussion) by a `Vote:` block:

```
Motion:   An implied motion to approve Ordinance 2024-13, as currently constituted,
          has been made by council rule.
...
Vote:     The motion was approved 5:1 with Councilors Christensen, Garrett, Handley,
          Hoban, and MacKay in favor. Bogdin opposed. Whipple excused.
```

Mapping applied:
- `in favor` → **aye**
- `opposed` / `against` / `voting no` → **nay**
- `excused` / `absent` → **absent**
- `abstain*` → **abstain**, `recus*` → **recuse**

`result` is the verbatim tally + computed outcome, e.g. `5:1 Pass`, `6-0 Pass`, `4:3 Fail`.
The tally separator (`:` vs `-`) is preserved from the source.

### Parsing heuristics (see code comments for detail)
- **Block model.** The file is scanned for three labels — agenda item headers (`^N.`),
  `Motion:`, `Vote:`. Each `Vote:` is paired with the nearest preceding `Motion:` and the
  nearest preceding item header (the item header supplies the motion description + drives
  `motion_type`). `motion_no` is the sequential ordinal of the vote within the meeting.
- **Vote-block boundary.** A vote statement is one contiguous paragraph, so gathering
  **stops at the first blank line** — continuing past it would absorb the following
  discussion paragraph and pull stray member names into the buckets. A belt-and-suspenders
  `truncate_vote_text()` also drops any trailing sentence with no tally/cue word.
- **Work-session "Vote:" alone on a line.** Some work sessions put `Vote:` on its own line
  with the result in the next paragraph; the gatherer skips the blank gap in that case.
- **Cue-anchored names.** Names are assigned to the **next** cue word that follows them, so
  "A, B, C in favor and D excused" correctly splits A/B/C → aye, D → absent (a naive
  period-split mis-bucketed D into aye). **Inverted phrasing** — a cue immediately followed
  by "were"/"was" ("Opposed were Shipley, Hoban and Ellsworth") — puts the names AFTER the
  cue; those are captured into that cue's bucket (bounded by the next cue / sentence end),
  then skipped so an adjacent cue can't re-bucket them (2 corpus instances: 2022-11-01 m5,
  2022-12-13 m10; fixed 2026-07-02, plan 3.5).
- **Tally detection.** Colon tallies (`7:0`) are unambiguous; dash tallies (`6-0`) are only
  honored when single-digit and not preceded by 3-4 digits (avoids ordinance/year ids like
  `2024-13`). Tallies with a side > 9 are rejected (kills video-timestamp leaks like `7:29`).
  `7:0with` (OCR glued the next word) still matches.
- **Mover / seconder.** Captured only when the minutes name them explicitly ("Councilor X
  made a motion / moved / motioned … seconded by Y"). The overwhelmingly common
  *"An implied motion … made by council rule"* has no mover/seconder by design → both `null`.

### names_recorded convention
- If the Vote line names members → `names_recorded:true`, lists filled verbatim.
- If the Vote line gives only a tally (e.g. `Approved 7:0 by unanimous consent`,
  `The motion passed 6-0 with a unanimous vote`) with **no names** → `names_recorded:false`
  and **all member lists are left empty. We never invent who voted which way.** These show
  up in `all_votes.csv` as a single member-less row carrying the motion + result.

### Motion-type taxonomy (fixed 12 categories)
`classify()` keys off the item text + motion text. Priority order matters: **Land-Use/Zoning**
is checked first (most Provo ordinances are rezones/plats/vacations/overlays and would
otherwise be swallowed by the generic "ordinance→Ordinance" rule). Then Budget Amendment /
Interlocal / Grant-Funding / Appointment / Contract-Purchase, then the generic Ordinance /
Resolution, then Ceremonial / Public Hearing Action / Procedural-Administrative, falling back
to **Other** (typically "A discussion regarding …" items that nonetheless carried a procedural
motion). Classification reads the agenda **item header** (untruncated) plus only the **first ~2
sentences of the motion text** — a `Motion:` block sometimes runs on into discussion with no
blank-line break, and deep-discussion words ("recommend", a stray "ordinance" mention) would
otherwise drive the category. Ceremonial keywords use word boundaries (so "commend" doesn't fire
inside "recommend"). Distribution across the 1071 motions:

```
359 Land-Use/Zoning   262 Resolution   160 Ordinance   107 Other   84 Appointment
 52 Procedural/Administrative   23 Interlocal   16 Budget Amendment   7 Grant-Funding
  3 Contract/Purchase   1 Public Hearing Action   0 Ceremonial
```

Ceremonial is **0** because Provo presents proclamations/recognitions in the opening ceremony
and does not take a recorded *vote* on them. A handful of edge cases (≈3) sit in
Contract/Purchase / Land-Use because a procedural motion happened to use a contract/"plan" word;
negligible at corpus scale.

## Roster (per-meeting, cross-checked against elections)

7 seats = 5 districts + 2 citywide, staggered. Surnames in vote lines are normalized to a
canonical "First Last" via the `ROSTER` map; spelling/OCR variants (`Filmore`→Fillmore,
`Garret`→Garrett, `Mackay/McKay`→MacKay, `Hadley`→Handley, `Christenson`→Christensen) via
`SURNAME_ALIASES`. The members observed in votes per year exactly match the election winners
in `../election_results/provo_results_by_candidate.csv`:

- **2020–2021:** Ellsworth, Fillmore, Handley, Harding, Hoban, Sewell, Shipley
- **2022–2023:** Harding & Sewell → **MacKay** (Citywide I, 2021) & **Whipple** (D5, 2021)
- **2024–2025:** Ellsworth/Fillmore/Shipley → **Bogdin** (D3), **Christensen** (D1),
  **Garrett** (Citywide II) — all 2023 winners
- **2026:** Handley (D2) → **Whitlock** (D2, 2025)

Council **staff** who appear by surname in the minutes (Dayley = Policy Analyst,
Zarbock = Budget Analyst, Allman = Recorder, Harrison, Jones, etc.) are deliberately **not**
in the roster map, so they are never miscounted as voters. Mayor **Kaufusi** is likewise not a
council member; she does, however, sit as a voting member of the **Board of Canvassers** (see
caveats).

## Validation

`votes/_validation_report.txt` flags every motion whose named-member count disagrees with the
printed tally (order-independent multiset compare, since Provo writes failed-motion tallies
majority-first, e.g. "failed 6:0 … opposed"). **Mismatches are logged, never auto-corrected**
— names are kept exactly as printed. The 12 current mismatches were all hand-reviewed:
- **Source typos** — minutes print a tally that disagrees with the names they list
  (e.g. 2023-05-02 m6 prints "5:0" but lists all 7 councilors in favor; 2023-06-06 prints
  "6:0" but lists 5 + 1 excused). Kept verbatim.
- **Board of Canvassers** — Mayor Kaufusi votes as an 8th board member; an "8:0" canvasser
  vote maps only the 7 council names (Kaufusi intentionally unmapped).
- **Double-listing** — 2022-02-15 m2 prints Handley in both the favor and the opposed clause.

## Known caveats / parse limitations
- **`pdf-ocr` file** (`2022-01-18_council-regular-meeting.md`) is OCR'd, lower fidelity
  (spacing artifacts like "Animplied", "7:0with"). It parses cleanly here (6 motions) because
  the parser tolerates glued tokens, but treat its text as less reliable than the born-digital
  files.
- **Tally-only motions (117).** Mostly `7:0` unanimous-consent and most **work-session**
  motions (which state a mover/seconder + tally but do not list individual aye names). These
  carry `names_recorded:false` by design.
- **No-tally motions (1).** 2022-02-15 m1: "The substitute motion failed with [names] in favor
  and [names] opposed" — no numeric tally printed; names captured, `result` = `Fail`.
- **Mover/seconder are mostly null** because Provo's standard "implied motion by council rule"
  records neither. They are populated for explicit motions (continuances, substitute motions,
  most work-session items).
- **Work sessions / retreats** hold far fewer recorded votes than regular meetings; some have
  none (the parser emits an empty `votes:[]` for them — not an error).
- The `motion` description is taken from the agenda **item header** when available (richer than
  the boilerplate "implied motion" text); trailing video timestamps (`0:15:08`) are stripped.

## Coverage (current run)
311 meetings · 1074 motions · 6255 member-vote rows · 957 named roll-calls ·
117 tally-only · 162 contested (≥1 nay/abstain/recuse) · 12 logged validation mismatches
(all explained above) · 0 unparsed meetings. **By `body`: Council 1015 motions / 5961 rows ·
RDA 59 motions / 404 rows (39 meetings) · CRA 0 · MBA 0.** 222 of the 311 meetings hold ≥1 recorded
vote; the other 89 are work sessions / retreats / town halls / budget hearings that take
no recorded action vote (they get an empty `votes:[]` JSON — not an error).


## 2026-07-17 — PMN crosscheck: 2024-07-23 Library-Board joint promoted
Promoted the 2024-07-23 Joint Meeting with Provo Library Board (PMN file 1220417) — a noticed
Municipal Council meeting the OnBase harvest lacked. Presentation-only → 0 motions (all_votes
unchanged). source=pmn/format=text; slug joint-meeting-with-provo-library-board. Two other
2023 joint-meeting leads were agenda-only (not promoted) — see pmn_backfill/CLAUDE.md.
