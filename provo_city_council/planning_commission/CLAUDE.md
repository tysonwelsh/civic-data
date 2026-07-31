# planning_commission/ — Provo City Planning Commission vote extraction

Structured roll-call vote data for the **Provo City Planning Commission (PC)**,
modeled on the council extractor in `../meeting_minutes/`. Entry point:
**`extract_votes.py`**. Data floor 2020, but **PC roll-call data exists 2025+
only** (see Coverage).

## What's here

| Path | Role |
|------|------|
| `minutes/<year>/<week-monday>/<date>_planning-commission-meeting.md` | Source minutes (agenda packet + appended Report of Action). 26 files, 2025-2026. Immutable input. |
| `minutes_index.csv` | Index of the 26 files (`date,year,title,slug,path,source,source_url,format,packet_url`). |
| `minutes_unrecovered.csv` | Documented retrieval gaps (2020-2024; see Coverage). |
| `extract_votes.py` | Parser. One JSON per meeting, rebuilds `all_votes.csv`, `roster.csv`, validation report. Resumable (`--force` re-extracts). |
| `validate_votes.py` | Independent QA (off-roster / out-of-range / JSON↔CSV reconcile / tally mismatches / coverage note). |
| `votes/<year>/<week>/<date>_planning-commission-meeting.json` | Structured intermediate, one per meeting (schema below). |
| `votes/_validation_report.txt` | Tally-vs-named-count cross-check + parse warnings. |
| `all_votes.csv` | Long format, one row per member-vote, rebuilt from the JSONs. Authoritative analysis table. |
| `roster.csv` | Reconstructed commissioner roster (`commissioner,first_seen,last_seen,n_meetings`). |

## Run

```bash
python3 planning_commission/extract_votes.py          # canonical 2025+ (resumable)
python3 planning_commission/extract_roa_votes.py      # merge recovered 2020-2024 ROAs + provenance (run AFTER extract_votes)
python3 planning_commission/validate_votes.py          # QA; exit 0 = PASS
```

## Coverage (2020+ — canonical minutes 2025+, recovered ROAs 2020-2024)

Provo began publishing **consolidated PC minutes** (the agenda packet with a
per-application *Report of Action* appended) in **2025**. For **2020-2024 there
are no PC minutes** on AgendaCenter (the year dropdown starts 2021 and only
posts agendas/packets, no minutes documents), and the OnBase portal
(`agendas.provo.gov`) has **no Planning Commission body** at all — a **SOURCE
limitation, not a parser gap** (`minutes_unrecovered.csv`). Canonical
(`extract_votes.py`) corpus: **26 meetings, 2025-02-26 → 2026-06-10, 102 motions.**

**2020-2024 now integrated from the recovered ROAs (2026-07-10).** The per-item
Reports of Action for 2020-2024 (recovered from Utah Public Notice into
`../pmn_backfill/`) are the SAME ROA format, so **`extract_roa_votes.py`** reuses
this parser over them and merges the result into `all_votes.csv`. Every row now
carries a **`provenance`** column: `minutes` (canonical, audited) vs `pmn_roa`
(recovered, additive — 381 motions / ~2,528 vote rows, 2020-01-08 → 2026-06-24,
filling dates the canonical minutes lack). The recovered rows flow through the db
(`motion.provenance`), `motions_std.csv`, `cities.db` (`v_contested_all.provenance`),
and enabled the previously-empty Council←PC referral + `v_pc_divergence` layers.
Recovered ROAs are born-digital; names are resolved by **full name** (folded onto
the 2025 roster only on first+surname match — surnames collide across eras, e.g.
Deborah Jensen vs Lisa Jensen). See `votes/_roa_extract_report.txt`.

## Provo PC "Report of Action" (ROA) format

Each minutes PDF is the agenda packet; the recorded votes live in the *Report of
Action* blocks appended at the end (one per application). A vote block:

```
                                 RECOMMENDED APPROVAL
On a vote of 7:0, the Planning Commission recommended that the Municipal Council
approve the above noted application.
Motion By: Lisa Jensen
Second By: Adam Shin
Votes in Favor of Motion: Lisa Jensen, Jonathon Hill, Melissa Kendall, ...
Votes Against the Motion: Barbara DeSoto, ...
Jonathon Hill was present as Chair.
```

Mapping:
- `Votes in Favor of Motion:` → **Aye**
- `Votes Against / Opposed / in Opposition / Not in Favor of the Motion:` → **Nay**
  (all four label variants + the "Montion" OCR typo are matched)
- prose `"<Name> voted against the motion."` → **Nay** (some ROAs state the lone
  dissenter in prose instead of a label)
- prose `"<Name> was excused" / "not feeling well ... excused" / "was absent"` → **Absent**
- `Motion By:` → mover, `Second By:` → seconder
- tally from `On a vote of N:N` (favor:against)
- **No abstain / recuse appear in the 2025-2026 corpus** (0 of 102 motions).

There are **multiple ROAs per meeting** (one per application); each becomes a
separate motion. `motion_no` is the sequential ordinal of the vote within the
meeting. Anchoring is **vote-first**: each `On a vote of N:N` is paired with the
nearest preceding `*ITEM N` line in its ROA (which supplies the motion
description + the `PL…` application id + drives `motion_type`).

### RECOMMENDATION vs FINAL ACTION — encoded in `result` and `action_class`

The ROA text states it explicitly. Legislative items (marked `*`) get an
advisory **recommendation** to the Municipal Council; administrative items (Project
Plan, Conditional Use, etc.) are the PC's **own final action**.

| ROA wording | `result` | `action_class` |
|---|---|---|
| "recommended that the Municipal Council **approve**" / "recommended **approval**" | `Positive recommendation N:N` | `pc_recommendation` |
| "recommended that the Municipal Council **deny**" / "recommended **denial**" | `Negative recommendation N:N` | `pc_recommendation` |
| "**approved** the above noted application" | `N:N Approved (Final Action)` | `pc_final_action` |
| "**denied** the above noted application" | `N:N Denied (Final Action)` | `pc_final_action` |
| "**continued** the above noted application" | `N:N Continued (Final Action)` | `pc_final_action` |
| "**tabled** …" | `N:N Tabled (Final Action)` | `pc_final_action` |
| (procedural fallback, none in corpus) | `N:N Pass` | `pc_final_action` |

**Downstream DB keying:** substring **`recommend`** in `result` → recommendation,
else final action; **`Positive`/`Negative`** gives direction. The explicit
`action_class` field on every JSON vote is the canonical signal.
*Deviation note:* the task's prescribed enum only named recommendation /
Approved / Denied / Pass. Continuances/tablings are the PC's own dispositions
(not advisory), so they are encoded as `… Continued/Tabled (Final Action)` rather
than collapsed to `Pass`, preserving the disposition while keeping the
`(Final Action)` convention. Distribution (102 motions): 50 Positive
recommendation, 34 Approved, 9 Negative recommendation, 5 Continued, 4 Denied.

### Board of Adjustment items
A few ROAs are **variance** decisions where the same commissioners sit as the
**Board of Adjustment** ("On a vote of 5:0, the Board of Adjustment denied …") —
analogous to the council recessing as the RDA. Per the task spec **`body` is
`PlanningCommission` on every row** (CSV + JSON); the acting capacity is recorded
in the JSON-only **`acting_body`** field (`PlanningCommission` | `BoardOfAdjustment`,
1 BoA item in corpus) and such items carry `motion_type=Variance`.

### Motion-type taxonomy (land-use oriented)
`classify()` keys off the application text first, the `PL…` code prefix as
fallback. Distribution (102 motions): 33 Project Plan, 24 Rezone, 21 Ordinance
Text Amendment, 7 General Plan Amendment, 5 Conditional Use Permit, 5
Subdivision/Plat, 4 Annexation, 2 Variance, 1 Vacation.

## Schemas

Per-meeting JSON:
```json
{"date":"2025-02-26","title":"Planning Commission",
 "source":"planning_commission/minutes/2025/2025-02-24/2025-02-26_planning-commission-meeting.md",
 "format":"text","parse_warnings":[],
 "votes":[{"motion_no":1,"motion":"*ITEM 1 Jon Jensen requests … PLOTA20240373",
           "body":"PlanningCommission","acting_body":"PlanningCommission",
           "pl_code":"PLOTA20240373","motion_type":"Ordinance Text Amendment",
           "action_class":"pc_recommendation","result":"Positive recommendation 4:3",
           "mover":"Melissa Kendall","seconder":"Lisa Jensen",
           "aye":["Adam Shin","Lisa Jensen","Jonathon Hill","Melissa Kendall"],
           "nay":["Barbara DeSoto","Daniel Gonzales","Anne Allen"],
           "abstain":[],"absent":[],"recuse":[],"names_recorded":true}]}
```

`all_votes.csv` (council column set + `provenance`):
`date,year,title,body,motion_no,motion,motion_type,result,mover,seconder,member,vote,source,provenance`
— one row per (motion × member); `vote` ∈ {Aye, Nay, Abstain, Absent, Recuse};
`provenance` ∈ {`minutes`, `pmn_roa`}. (Running `extract_votes.py` alone writes the
13-col canonical CSV; `extract_roa_votes.py` adds the `provenance` column + ROA rows.)
`body="PlanningCommission"` and `title="Planning Commission"` on every row. (The
JSON-only `acting_body`/`pl_code`/`action_class` fields are not in the CSV to keep
the column set identical to the council table.)

## Roster (appointed; no election)

12 commissioners reconstructed from ROA name lists + Chair attribution + mover/
seconder. **Surnames are unique across the roster**, so names map primarily on
surname; the first name is used only to disambiguate/catch garbles. Folded
variants:
- **First-name OCR/typos:** Jonathon Hill (`Jonathan`/`Johnathan`/`Johathan`/`Jonhathan`),
  Daniel Gonzales (`Daneil`), Barbara DeSoto (`Barabara`), Matt Wheelwright
  (`Matthew`), Jon Lyons (`John`), Jeff Whitlock (`Jeffrey`).
- **Full-name alias:** `Anne Black` → **Anne Allen** (appears exactly once,
  2025-02-26 Item 1; Anne Allen is the only "Anne" across all 26 meetings and it
  reconciles that 4:3 vote — a clear transcription error, folded like the
  council's `Filmore→Fillmore`).
- **Ambiguous, NOT mapped:** `Melissa Jensen` (2026-04-22) — surname→Lisa Jensen
  but first name→Melissa Kendall (two different sitting members). Per the cardinal
  rule this garble is **skipped, never guessed**; the remaining 5 named ayes
  reconcile the printed 5:0. Logged in the validation report's PARSE WARNINGS.

Roster (n_meetings): Jonathon Hill 25 · Lisa Jensen 23 · Melissa Kendall 22 ·
Barbara DeSoto 19 · Daniel Gonzales 17 · Anne Allen 16 · Joel Temple 15 · Matt
Wheelwright 15 · Jon Lyons 14 · Andrew South 6 · Adam Shin 3 · Jeff Whitlock 1.
(Turnover mid-2025: Adam Shin & Andrew South roll off; Joel Temple, Matt
Wheelwright, Jon Lyons join.) Jonathon Hill chairs almost every meeting.

### Appointment cross-check (council ↔ PC)
PC members are **appointed by the Mayor with Municipal Council consent** (no
election). The only PC-appointment action in the council corpus
(`../meeting_minutes/all_votes.csv`, `motion_type=Appointment`) is **2021-11-16,
Resolution 2021-40** "consenting to the appointment of individuals to the Planning
Commission" — which **predates the 2025+ PC voting window**, so it names none of
the 12 commissioners above. No per-commissioner appointment date is recoverable
from the council minutes for the current PC roster; first_seen in `roster.csv` is
the earliest meeting each member is observed voting.

**Q3-2026 refresh (2026-07-19):** a **13th commissioner, Tosh Metzger**, first
appears 2026-07-08 and was added to the hardcoded `ROSTER`/`FIRSTNAMES` maps in
`extract_votes.py` (surname `metzger`, first name `tosh` — both unique). Before the
add he was silently dropped as off-roster, which understated every 2026-07-08 named
tally by one (5 spurious tally mismatches); re-extraction with `--force` reconciles
all five. The roster/meeting/motion counts elsewhere in this file predate the
2020-2024 ROA backfill and this add — `roster.csv` is authoritative.

## Validation

`validate_votes.py` / `votes/_validation_report.txt`: **0 off-roster, 0
out-of-range, JSON↔CSV reconciles (673 member rows)**. **3 tally-vs-named-count
mismatches** remain — all **genuine source discrepancies** where the printed
tally names *more* voters than the minutes actually list (the unnamed voter
cannot be guessed, per the cardinal rule). Kept verbatim:
- `2026-05-13 m5` 5:3 — only 4 ayes named (5th unnamed).
- `2026-05-13 m6` 6:2 — only 5 ayes named (6th unnamed).
- `2026-06-10 m2` 5:1 — recommend-denial, the lone dissenter is unnamed.

There are **0 tally-only motions** — every ROA in the corpus names its voters.

## Coverage summary (current run)
26 meetings · 102 motions · 673 member-vote rows · 59 recommendations · 43 final
actions (1 Board-of-Adjustment variance) · 22 contested (≥1 Nay) · 0 tally-only ·
12 distinct commissioners · 3 documented tally mismatches · 0 unparsed. **PC data
2025+ only** (2020-2024 not published by the city).
