# Orem City Council — vote extraction pipeline

This folder holds the Orem City Council meeting minutes (markdown) and the roll-call
votes extracted from them. Everything derived is regenerable from the minutes by
re-running `extract_votes.py`.

## Layout

```
meeting_minutes/
├── minutes_index.csv                # one row per meeting (date,year,title,slug,path,source,source_url,format)
├── minutes/<year>/<week-monday>/<date>_<slug>.md   # 130 source minutes files
├── extract_votes.py                 # the parser/pipeline (run from anywhere)
├── all_votes.csv                    # LONG format: one row per member-vote (rebuilt by the script)
├── votes/<year>/<week>/<date>_<slug>.json   # per-meeting structured intermediate (130 files)
├── votes/_validation_report.txt     # tally-consistency + roster-vs-election cross-check
└── CLAUDE.md                        # this file
```

`all_votes.csv` is always rebuilt from the per-meeting JSONs; the JSONs are the structured
source of truth. Re-running the script is idempotent (it overwrites JSONs + CSV).

Run: `python3 meeting_minutes/extract_votes.py`

## Current results (last run)

- **meetings_processed: 130** (every index row; all 130 now have real body text — 0 stubs)
- **motions_extracted: 567** (566 named roll-calls + 1 tally-only)
- **member_vote_rows: 3749**
- **named_rollcall_motions: 566** · **tally_only_motions: 1** · **contested_motions: 49**
- **validation_mismatches: 0**
- **roster: exactly 7 members every year 2020–2026** (6 council + mayor)
- **127 of 130 meetings produced votes** (3 vote-less are correct — see below)
- **by `body` (motions / member-vote rows):** Council 542 / 3602 · RDA 15 / 91 ·
  SSLD 9 / 51 · MBA 1 / 5. (CRA: 0 — Orem uses RDA, not the post-2016 CRA name; the lone
  "Community Reinvestment Area" mention is a *project area* inside an RDA budget, not a body.)
  All 49 contested motions are `Council`; RDA/SSLD/MBA business is 100% unanimous.

## How Orem records votes (the formats the parser handles)

Each motion is written in prose. The authoritative per-motion vote is the
**"Those voting …"** clause:

```
Mr. Macdonald moved to approve the Consent Agenda as listed. Mrs. Lauret seconded the
motion. Those voting aye: Richard F. Brunst, Jeff Lambson, Debby Lauret, Tom Macdonald,
Terry Peterson, David Spencer, and Brent Sumner. The motion passed.
```

Variations seen across 2020–2026 (all handled):
- **aye/nay wording:** `Those voting aye:` / `Those voting yes:` and `Those voting nay:` /
  `Those voting no:`. `Those voting no: None.` is treated as an empty nay list.
- **mover:** `X moved to …`, `X moved, by ordinance/resolution, to …`, `Mayor Brunst
  then moved …` (optional adverb), `X moved …, seconded by Y`.
- **seconder:** `Y seconded the motion`, `Seconded by Y`, `seconded by Y`, any case.
- **markdown bold** around cue words in 2024 files: `**Mr. Macdonald moved** … **Seconded by** …`.
- **name lists wrap across page breaks** with a page-footer line injected mid-list
  (`City Council Minutes – … www.orem.org/meetings`, `DRAFT`, `(p.5)`). The parser strips
  those footers and flattens whitespace *before* matching, so wrapped lists rejoin.
- **trailing signature page** (`COUNCIL MEMBER | AYE | NAY | ABSTAIN [| ABSENT]`, sometimes
  with ☑ checkboxes) is a single meeting-level sign-off, **NOT** a per-motion vote — it is
  **ignored** (the prose `Those voting` clauses are authoritative).

### Tally-only / unanimous-without-names
A second pass catches `X moved … Y seconded … The motion passed[ unanimously].` blocks that
have **no** `Those voting` name list. These are recorded with `names_recorded:false`, empty
member lists, and `result` = bare `Pass`/`Fail` (no `n-m` tally, since per-member data is
absent). **We never invent who voted which way.** Only **1** such motion exists in the whole
corpus (2020-04-28 adjournment).

## Schema

Per-meeting JSON (each vote carries `body`):
```json
{"date":"2020-01-14","title":"City Council Meeting","source":"meeting_minutes/minutes/2020/…/….md",
 "votes":[{"motion_no":1,"motion":"…","body":"Council","motion_type":"Ordinance","result":"6-1 Pass",
           "mover":"Tom Macdonald","seconder":"Debby Lauret","names_recorded":true,
           "aye":["…"],"nay":["…"],"abstain":[],"absent":[],"recuse":[]}]}
```
`all_votes.csv` columns: `date,year,title,body,motion_no,motion,motion_type,result,mover,
seconder,member,vote,source` — one row per member-vote, `vote ∈ {Aye,Nay,Abstain,Absent,
Recuse}`. (In practice Orem prose only yields **Aye/Nay** — see below.)

### `body` — which governing body took the vote
`body ∈ {Council (default), RDA, MBA, SSLD}` (also supports `CRA`, none in Orem). In Utah the
City Council sits **as the board** of the Redevelopment Agency (RDA), Municipal Building
Authority (MBA), etc. — **same 7 people, same night**. Orem does **not** publish separate
RDA/MBA meeting files; instead, mid-meeting, the council *adjourns to a meeting of* the other
body: `ADJOURN TO A MEETING OF THE OREM REDEVELOPMENT AGENCY (RDA)` → `Mr. X moved to adjourn
to a meeting of the Orem Redevelopment Agency …`. After that transition motion, the embedded
section (`RDA CONSENT ITEMS`, `RDA SCHEDULED ITEMS`, the RDA budget/minutes votes) is that
body's business **until the next "adjourn to a meeting of …" marker or the final adjournment**.
Bodies run in sequence (RDA → SSLD → MBA); Orem never "reconvenes as the City Council."

Tagging mechanics (`find_body_markers` / `body_at` in `extract_votes.py`):
- The marker regex `BODY_MARKER_RE` matches "adjourn(ment) to a meeting of the &lt;body&gt;"
  in the flattened text and maps the captured name to a code (`body_from_who`):
  Redevelopment Agency/RDA → `RDA`, Municipal Building Authority/MBA → `MBA`, Community
  Reinvestment Agency/CRA → `CRA`, Special Service(s) Lighting District/SSLD → `SSLD`.
- The **transition motion itself** ("moved to adjourn to a meeting of X") is a **Council**
  vote — the council, still sitting as the council, deciding to convene as the next body — so
  it keeps the PRIOR body. We anchor each body change at the END of that transition motion's
  vote block (the first `The motion passed/failed.` after the marker), so only the section's
  *subsequent* motions flip to the new body. Each motion's body = the most recent marker
  anchor ≤ its `block_start`, else `Council`.
- **Role synonyms map to the same people:** in board capacity the minutes still list the same
  names in the `Those voting` clause, so no new members appear — verified: the set of
  RDA/MBA/SSLD voters is a strict subset of the Council roster (0 members only in a non-Council
  body). Board-role titles ("Board Member"/"Chair"/"Agency Member") resolve via the same
  surname-keyed `CANON` as "Councilmember"/"Mayor".
- A **narrative mention** of a body (e.g. discussing "Municipal Building Authority property"
  or the "Community Reinvestment Area") does **not** trigger a body change — only the explicit
  "adjourn to a meeting of …" motion does — so such a council item correctly stays `Council`.

**SSLD note:** Orem's Special Service Lighting District is a real separate special district
(outside the RDA/CRA/MBA set). Its motions are tagged `SSLD` rather than mislabeled `Council`.
For **council-only** analysis, filter `body=Council`. No separate RDA/MBA/SSLD *meeting files*
exist or are missing — all such business is embedded in council files, all present on disk
(referenced prior-body minute dates — May 13 2025, June 18 2024, "June 1"[=10] 2025 — each
resolve to an on-disk council file with an embedded section).

`result` is computed from the parsed lists: `<#aye>-<#nay> Pass|Fail` for named motions,
bare `Pass|Fail` for tally-only. The `Pass|Fail` word comes from the verbatim `The motion
passed/failed/carried/…` outcome in the minutes.

## Does the mayor vote? YES

Orem is council-manager with **6 at-large council members + an elected Mayor**. The Mayor's
name appears in the aye/nay lists of essentially every motion (Brunst 2020–21, David Young
2022–25, then McCandless), and the Mayor frequently is the **mover** (e.g. "Mayor Brunst
moved, by ordinance, …"). So the Mayor is a full voting member and the roster size is **7**.
This is confirmed by every yearly roster being exactly 7.

## motion_type mapping (fixed 12-category taxonomy)

Classification reads the **motion text first**, then the agenda heading, in this order
(first match wins) — text-first so a "approve the Consent Agenda" motion sitting under an
ORDINANCE heading is not mis-filed:

1. `Procedural/Administrative` — adjourn; consent agenda/items; table/continue/postpone/
   recess/excuse; approve … minutes; **canvass / certify … election**; closed (executive)
   meeting; agenda-order changes.
2. `Appointment` — appoint / reappoint (boards & commissions).
3. `Ceremonial` — proclamation / proclaim / recognize / honor.
4. `Interlocal` — interlocal / inter-local agreement.
5. `Budget Amendment` — "budget amendment" or budget+amend.
6. `Grant-Funding` — grant+fund/award/accept/cdbg, or CDBG/CARES-ACT funding.
7. `Land-Use/Zoning` — rezone / annex / general plan / subdivision / plat / conditional
   use / zoning map / land use.
8. `Ordinance` — "ordinance"; or a code/text amendment ("amend … Section/Article/Appendix
   /City Code") even when the truncated text drops the word "ordinance".
9. `Resolution` — "resolution".
10. `Contract/Purchase` — contract / agreement / purchase / bid / procure / professional
    services / task order / change order.
11. `Public Hearing Action` — a bare public-hearing open/close with no substantive motion
    (rare in Orem; the open/close is usually narrative, not a vote → almost never fires).
12. `Other` — fallback (4 motions; genuinely ambiguous/odd wording).

Last-run distribution: Procedural/Administrative 275, Ordinance 62, Resolution 57,
Land-Use/Zoning 55, Appointment 55, Budget Amendment 19, Grant-Funding 17, Other 15,
Contract/Purchase 7, Interlocal 2, Ceremonial 2.

**The analytical signal is the 49 contested motions** (any Nay) — listed in the validation
report. Orem records **only Aye/Nay** in prose; no abstain/recuse/absent vote-block wording
appears anywhere in the corpus, so those CSV `vote` values never occur here.

## Name normalization

Names are keyed on surname and canonicalized to one `First Last` spelling, resolving the
documented Orem drift and OCR variants:
- Millet / Millett / **Millettt** → **LaNae Millett**
- Macdonald / McDonald / **Macdonals** (OCR 's'-for-'d') → **Tom Macdonald**
- Debby / Debbie Lauret → **Debby Lauret**
- Spencer / **Spender** / **Spenser** (OCR) → **David Spencer**
- Gale / **Jenn'Gale** (OCR, no separating space) → **Jenn Gale**

OCR also injects stray punctuation into the vote labels themselves — `Those voting yes:.`
(stray period, 2026-03-10), `Those voting.no:` and `The.motion failed.` (period-for-space,
2024-12-10). The vote-block regex tolerates a `[\s.:]`/`[\s.]` run in the label and the
`The…motion` outcome cue so these still parse and self-terminate (a non-tolerant outcome
cue previously merged two roll-calls into one motion with duplicate members). A bare title
token (`Mr`/`Mr.`) left behind when an OCR period slices a surname off
(`Those voting nay: Mr. Macdonald`) is protected from the sentence-cut and resolved to the
surname rather than emitted as a bogus `Mr` member.

Titled short forms in mover/seconder ("Mr. Spencer", "Mrs. Lauret", "Mayor Young",
"Mr.Spencer" with no space, "M. Macdonald") are stripped to the surname and resolved.
A noisy mover/seconder capture (e.g. "Pm Mr. Spender", "as listed. Mrs. Millettt") is
cleaned by scanning right-to-left for a known roster surname (`resolve_actor`).

To add a newly-elected member or a new spelling, extend the `CANON` dict in
`extract_votes.py`.

## Roster vs election cross-check

The validation report lists each year's roster and flags members not matched to an
`is_winner` row (won the election in year-0…year-4) in
`election_results/orem_results_by_candidate.csv`. Expected unmatched names are pre-2020
incumbents whose winning elections (2017/2019) predate or sit outside the loaded election
data window (Brent Sumner, Richard Brunst, Tom Macdonald in 2020) — these are real members,
just not in the election CSV's covered years. This is a sanity flag, not an error.

## OCR caveat

`minutes/2025/2025-11-17/2025-11-18_city-council.md` is **OCR'd** (lower fidelity; footer
text like "Mayof f", "eresa McKitrick", `(These minutes were created with the help of AI)`).
It still parses cleanly: 4 motions, all 7-0, movers/seconders correct, because the
`moved … Seconded by … Those voting yes:` structure survived OCR. Spot-checked by hand.

## Content coverage / known non-failures

All **130 indexed meetings now have real body text** (the earlier content-empty stubs have
since been re-fetched with full minutes), so there are **0 stubs**. Every meeting parses.

Of the 130 content files, **127 produced votes**; the 3 that did not are correct:
- `2021-01-23_city-council-retreat` — a retreat, no formal votes.
- `2024-05-07` — a four-city joint/TSD discussion meeting, adjourned with no recorded vote.
- `2026-04-15_tsd-and-city-council` — a joint TSD/Council discussion meeting, no recorded vote.

(`2020-04-28` is captured: its only motion is the tally-only adjournment with
`names_recorded:false`, so the JSON has 1 vote but no member rows in the CSV.)

## Validation performed

- **Per-motion consistency:** outcome word vs aye>nay; no member in both aye & nay; ≤7
  voters; non-empty lists when `names_recorded`. **0 mismatches.**
- **Hand spot-checks (5 meetings) vs source minutes — all exact:** 2020-07-14 (6 motions,
  two contested 3-4 Fail / 5-2 Pass), 2025-11-18 (OCR, 4 motions), 2024-09-17 (markdown
  bold), 2022-08-02 (contested 4-3 school-district resolution), 2021-08-09 (special,
  contested 4-3 land-use).
