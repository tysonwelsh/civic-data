# meeting_minutes/ — vote extraction pipeline (St. George, UT)

## What's here
- `minutes/<year>/<week-monday>/<date>_<slug>.md` — **305 born-digital minutes
  (2020–2026)**: 214 for 2022–2026 from Revize PDFs + 91 for 2020–2021 backfilled from
  the Utah Public Notice (PMN) live search API. Immutable source of truth.
  One meeting is unrecoverable: the 2025-10-09 Work Meeting's published minutes PDF is a
  city-side mis-upload (byte-identical to the 2025-10-16 Regular Meeting minutes on both
  Revize and PMN) — removed 2026-07-02; see `minutes_unrecovered.csv` and `../VERIFICATION.md`.
- `minutes_index.csv` — index of all 305 files (`date,year,title,slug,path,source,source_url,format`;
  `source` = `revize` for 2022–26, `pmn` for 2020–21).
- `extract_votes.py` — the extractor (below).
- `votes/<year>/<week>/<date>_<slug>.json` — per-meeting structured votes.
- `votes/_validation_report.txt` — tally-vs-outcome cross-check log.
- `all_votes.csv` — long format, one row per member-vote (rebuilt from the JSONs).
  Columns: `date,year,title,body,motion_no,motion,motion_type,result,mover,seconder,member,vote,source`.
  **`body`** (added after `title`) names the governing body that took the vote — see
  "Body tagging" below. For council-vote analysis, **filter `body=Council`**.

## Run
```
python3 meeting_minutes/extract_votes.py
```
Reprocesses all meetings and rebuilds `all_votes.csv` + the validation report
from `minutes/` every time (idempotent; not incremental — the corpus is small).

## Coverage
- **2020–2026 (305 meetings)** — every month from 2020-01 through 2026-06 has a council
  meeting. 2022–26 from Revize; **2020–21 backfilled from the PMN live search API**
  (`POST /pmn/searchresult.html`, JSON body, CSRF from `search.html` meta, `sortColumn`/
  `sortOrder` MUST be empty; body 241 = St. George City Council). See `recon.md`.
- Latest run (2026-07-19): 1,801 motions, **8,464 member-vote rows** (8,382 `body=Council`
  + 19 RDA + 40 ArtsCommission + 10 Canvass; +13 blank-member placeholder rows for
  died/withdrawn/superseded motions), 85 contested, 2 tally-vs-result mismatches (both
  pre-existing council quirks: minutes say "unanimous" but a nay was recorded — 2021-06-03
  m7, 2021-11-18 m15). NOTE: 2020–21 minutes render `MOTION:`/`SECOND:`/`VOTE:` headers inline
  (vs standalone in 2022+) — the 91 backfilled files were normalized (header split onto its
  own line) so the shared parser works. 2020–21 member names are bare surnames (verified
  real officials; cosmetic vs the "First Last" form used in 2022+).
- **Two extraction-format tolerances added 2026-07-19** (`_strip_line_number_gutter` +
  `_split_inline_headers`, gated per-file so non-affected files stay byte-identical):
  - **Line-number gutter** — one council file, **2022-08-25 RDA**, is a born-digital PDF
    printed with a left-margin per-page line-number gutter (`25         MOTION:`) that
    defeated the standalone-header regexes (0 motions). The detector (leading-number
    fraction + sequential-increment test; affected files score frac 0.68–0.81, every other
    file 0.00) strips the gutter → recovered the RDA adjourn 4-0 (Hughes/McArthur/Larsen/
    Tanner). (The PC sibling extractor carries the same fix — see planning_commission.)
  - **Inline headers** — **2022-01-03** (swearing-in regular meeting) printed
    `MOTION:  <text>` on one line; the splitter (only file in the council corpus with this
    layout) recovered its 2 motions (appoint city officers 5-0; adjourn 5-0), all five
    Councilmembers named — a genuinely-uncaptured roll (verified vs source).

## Why parsing is easy here
St. George minutes use an exceptionally regular block:
```
MOTION:
      A motion was made by Councilmember <Name> to <text>.
SECOND:
      The motion was seconded by Councilmember <Name>.
VOTE:
      Mayor <Name> called for a (roll call) vote, as follows:
          Councilmember <Name> – aye|nay|abstain|absent
          ...
      The vote was unanimous and the motion carried.   (or "The motion failed.")
```
Council votes are **always per-member roll-call** — there are NO numeric
tally-only council votes (the `5-0`/`7-0` numbers that appear in the text are
narrative *Planning Commission recommendations*, never the council's own vote).

## Heuristics & edge cases handled
- **En-dash AND hyphen** both used in `Councilmember X – aye` / `- aye`.
- **Mayor normally does NOT vote**; the Mayor appears in a vote line only to break
  a tie (e.g. 2025-02-20: 3-2 with `Mayor Randall – aye`, `Tanner – absent`). The
  parser counts whoever is listed, so a Mayor tie-break is captured correctly.
- **Vote values**: `aye→Aye`, `nay→Nay`, `abstain→Abstain`, `absent`/`excused→Absent`,
  `recused himself`/`recused herself→Recuse`.
- **OCR transposition** `Councilmember to Larsen` (the word "to" landing before the
  surname) is tolerated in mover/seconder regex.
- **Name typos** mapped: `Lasen`/`Larson → Natalie Larsen`.
- **Amended / superseded motions**: a `MOTION:` with no following `VOTE:` (replaced
  by an `AMENDED MOTION:` that *is* voted) is skipped — only the motion that
  actually reached a vote gets a `motion_no`. So `motion_no` count can be < the raw
  `MOTION:` header count in a file (by design).
- **Page-break noise** (`St. George City Council Minutes` / `Page Four` / a stray
  date line) inside a vote block is stripped.
- `result` is built as `<aye>-<nay> Pass|Fail (<verbatim outcome>)` when members are
  named; for tally-only it is the verbatim outcome string.

## Name normalization
Surname → canonical "First Last" via `SURNAME_TO_FULL` in the script. Roster
cross-checked against `election_results/st_george_results_by_candidate.csv` winners:
- **2022–2023**: Hughes, McArthur, Larkin, Larsen, Tanner (Mayor **Randall**).
- **2024–2025**: McArthur replaced by **Kemp** (Kemp & Hughes won Nov 2023; Hughes
  stayed a councilmember). Mayor still **Randall**.
- **2026**: **Hughes** became Mayor (won Nov 2025); **Anderson** appointed Jan 2026
  to fill Hughes's vacated council seat → Larkin, Larsen, Tanner, Kemp, Anderson.
- **2020–2021** (earlier roster, also mapped): Mayor **Jon Pike**, plus **Vardell Curtis**,
  **Bryan Smethurst**, **Bette Arial** (cross-checked vs election winners).
`SURNAME_TO_FULL` mapping is applied **only for council-as-board bodies** (see Body tagging)
— Arts/Planning Commission surnames are intentionally left unmapped. Each per-meeting JSON
also stores `roster_present` parsed from the `PRESENT:` block (council roles only;
separate-commission members are excluded so they don't pollute the council roster).

## `names_recorded` convention
`true` when the VOTE block lists individual members; `false` when only a tally/outcome
is given. Per the extraction standards we **never invent who voted which way** — a
`names_recorded:false` motion contributes a JSON record but **zero rows** to
`all_votes.csv` (no member to attribute).

## Body tagging — the `body` column (READ THIS for any vote analysis)
The minutes folder mixes the core City Council with several adjacent bodies published in
the same portal. Every vote row carries a **`body`** column (emitted after `title`) so
each body is filterable. **For council-vote analysis, filter `body=Council`.** Values:

| `body` | what it is | who votes | name handling |
|--------|-----------|-----------|---------------|
| `Council` | St. George City Council (the core dataset) | Councilmembers + Mayor | canonical "First Last" |
| `RDA` | Neighborhood Redevelopment Agency | the **council sitting AS the board** — SAME people | board roles ("Agency Member", "Chairwoman") **mapped to the council member names** |
| `Canvass` | Board of Canvassers (certifies an election) | the **council as the canvass board** — SAME people | council member names |
| `CRA` / `MBA` | Community Reinvestment Agency / Municipal Building Authority | council-as-board (none have appeared yet in the corpus) | council member names |
| `ArtsCommission` | St. George Arts Commission | a **SEPARATE body — DIFFERENT people** (Wilson-Spooner, Kessler, Mast, Webb, Schmidt, Nelson, Scharf, …) | kept as their **own** names — **NOT** merged with councilmembers |
| `PlanningCommission` | Planning Commission | a **SEPARATE body — DIFFERENT people** (Draper, West, Chapman, Fisher, Rogers, …) | own names (no PC-only roll-call votes have appeared yet; PC sessions in the corpus are work meetings, and joint PC+CC meetings record *councilmember* votes → tagged `Council`) |

**Council vs council-as-board:** `Council` + `RDA`/`CRA`/`MBA`/`Canvass` are all the SAME
people (the council in a different capacity), so `body ∈ {Council,RDA,CRA,MBA,Canvass}` is
the full council population. Validated: RDA & Canvass member sets ⊆ the Council member set.
**Arts/Planning Commission are genuinely different people** — validated disjoint from the
council roster; the parser deliberately does **not** normalize their surnames to
councilmember names (don't pretend a Commission Member is a councilmember).

### How `body` is derived (`extract_votes.py`)
1. `classify_body_from_title()` seeds a per-meeting default from the index `title`
   (e.g. `Rda ...` → RDA, `... Canvass ...` → Canvass, `Arts Commission` → ArtsCommission).
2. Per motion, the **voter role in the roll call wins** (`role_to_body()`): an
   "Agency Member" block → RDA, a "Commission Member" block → ArtsCommission, even inside a
   differently-titled file. Council roll-calls in a joint Council/Commission meeting → Council.
3. A dedicated council-as-board meeting (Canvass/RDA/CRA/MBA) often addresses its members as
   "Councilmember" in the roll call; when the role says Council but the *meeting* is a
   council-as-board session, the meeting's board identity wins (Council → Canvass/RDA).
4. `normalize_name(surname, body)` maps to canonical council names **only** for council-as-
   board bodies; separate-body surnames stay as-is.

Earlier note that RDA/Arts roll-calls landed as tally-only (`names_recorded:false`) is
**obsolete** — the parser now recognizes "Agency Member"/"Commission Member"/"Chairwoman"
roll-call lines, so those votes are fully named (0 tally-only motions this run).

## motion_type mapping (fixed 12-category taxonomy)
`classify_motion()` reads the ALLCAPS agenda section header (e.g.
`ZONE CHANGE/ORDINANCE:`, `PETITION FOR ANNEXATION/RESOLUTION:`) plus the motion text.
Precedence (first match wins):
1. **Procedural/Administrative** — adjourn/recess, consent calendar, approve minutes.
2. **Public Hearing Action** — open/close/continue a public hearing.
3. **Land-Use/Zoning** — zone change, plat/subdivision, annexation, PD, hillside,
   conditional use, general plan, ROW/easement vacate. (Most common: 467 rows.)
4. **Budget Amendment** → 5. **Grant-Funding** (incl. RAP Tax) → 6. **Interlocal**
   → 7. **Appointment** (incl. board reps, swearing-in, fill vacancy) →
   8. **Contract/Purchase** (contract/bid/agreement/lease/MOU) → 9. **Ceremonial**.
10. Generic **Ordinance** / **Resolution** by the instrument named (checked late so
    land-use ordinances stay Land-Use/Zoning).
11. **Other** fallback.

## Validation
`extract_votes.py` cross-checks each named tally against the verbatim outcome and logs
to `votes/_validation_report.txt`:
- "unanimous" claimed but a nay recorded,
- "carried/passed" but nay > aye,
- "failed" but aye > nay.
Latest run: **2 mismatches** (both pre-existing council quirks where the minutes write
"unanimous" yet a nay is in the roll call — 2021-06-03 m7, 2021-11-18 m15; reported, not
guessed). Body spot-checks vs source: RDA 2023-09-21 & 2022-03-10 (Agency Members → council
names, body=RDA), Arts 2023-12-07 (Commission Members kept as own names, body=ArtsCommission)
all matched.

## Known parse limitations
- Adjacent-body roll-calls (RDA "Agency Member", Arts "Commission Member", "Chairwoman")
  are now parsed and named like council votes (see Body tagging); their `body` is tagged
  accordingly. No tally-only motions in the latest run.
- `motion` text is the verbatim "A motion was made by..." sentence; the agenda
  `section` header is stored separately for context/typing. Very long motions with
  embedded numbered conditions are captured in full (whitespace-collapsed).
