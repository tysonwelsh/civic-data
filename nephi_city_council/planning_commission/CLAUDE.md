# planning_commission/ — Nephi City Planning Commission vote extraction

Turns 70 Planning-Commission minutes markdown files (2020–2026) into structured motion data,
modeled on `../meeting_minutes/` (the City Council extractor). Entry point: **`extract_votes.py`**.

## What's here
| Path | Role |
|------|------|
| `minutes/<year>/<week-monday>/<date>_planning-commission-meeting.md` | Source minutes (66 born-digital text PDFs + 4 .docx + 1 OCR → markdown). Immutable input. |
| `minutes_index.csv` | Index of the 70 files (`date,year,title,slug,path,source,source_url,format`). |
| `extract_votes.py` | Parser → per-meeting JSON + `all_votes.csv` + `roster.csv`. |
| `validate_votes.py` | QA: off-roster check, JSON↔CSV reconcile, schema, narrative-share note. |
| `votes/<year>/<week>/<date>_planning-commission-meeting.json` | Structured intermediate, one per meeting. |
| `all_votes.csv` | Long format. **Authoritative analysis table.** Same 13-col schema as the Council. |
| `roster.csv` | Commissioners (`commissioner,first_seen,last_seen,n_meetings`). |

## Run
```bash
python3 planning_commission/extract_votes.py          # resumable; skips existing JSON
python3 planning_commission/extract_votes.py --force   # re-extract all
python3 planning_commission/validate_votes.py          # must print "VALIDATION: PASS"
```

## Schema (identical to `meeting_minutes/all_votes.csv`)
`date,year,title,body,motion_no,motion,motion_type,result,mover,seconder,member,vote,source`
Every row has **`body="PlanningCommission"`** and **`title="Planning Commission"`**.

## Two minute formats, both narrative-dominant
- **2020–2021: pure narrative** — `"<Name> motioned to <action>. <Name> seconded. Motion passed
  on a unanimous vote."` (mover may trail: `"on a motion by <Name> and a second by <Name>"`).
- **2022–2026: structured** action blocks — a `Motion:`/`Made by:` line, a `Second:`/`Seconded:`
  line, and an `Outcome:` line (often multi-line in 2024+):
  ```
  a. Motion: Commissioner <Name> motions that <action>.
  b. Second: Commissioner <Name> seconded the motion.
  c. Outcome: Unanimously approved, Motion Passes.
  ```
  Verbs seen: approved / passes / passed / carries / denied / unanimous (NOT just "passed").

**Most motions are tally-only** → `names_recorded:false`, one summary row carrying
mover + seconder + result + motion. We **never** infer who voted which way from a "unanimous"
result. Per-member rows appear ONLY where the minutes name voters: a roll call, an
`Opposed:`/`Nay:` label, or an inline narrative dissent. (Coverage below: 12 of 331 motions name
voters; the rest are narrative tally-only — the expected pattern for a small rural commission.)

## `result` encodes RECOMMENDATION vs FINAL ACTION vs PROCEDURAL (machine-detectable)
The PC **forwards recommendations** to the City Council, and takes **final action** on some items.
The disposition is written into `result` so the DB can classify without re-reading the motion:

| Class | `result` form | When |
|-------|---------------|------|
| **Recommendation** | `Positive recommendation` / `Negative recommendation` (+ ` N:N` iff tallied) | motion says recommend/forward to Council, OR is a rezone / zone change / plat / subdivision / annexation / general-plan / ordinance or code amendment |
| **Final action** | `N:N Approved (Final Action)` / `Denied (Final Action)` (N:N is a **prefix** here) | conditional-use / home-occupation permit, site plan, business license, sign permit, lot-line / boundary adjustment |
| **Procedural** | `N:N Pass` / `Fail` | minutes, agenda, adjourn, elect/nominate officers, table/postpone/continue, schedule a hearing |

Rules:
- **`N:N` is included ONLY when the ayes were actually enumerated** (a real roll call). A
  dissent-only record (`Opposed:` / `Nay:` / narrative "X opposed") keeps the dissenter name but
  **no tally** — e.g. `Positive recommendation (Fran Petersen opposed)` — because the aye count
  was not recorded. We never invent counts.
- `(unanimous)` is appended only when the minutes say so **and** there is no recorded dissent.
- A motion to **deny / recommend denial** is read by intent: `result` direction words
  (Positive/Negative, Approved/Denied) reflect the *effect*, oriented by the outcome.

## Name normalization & the Peterson/Petersen split
13 canonical commissioners (see `FIRST_CANON`/`LAST_CANON` in the script). Role words
(Commissioner/Chairman/Alternate/…) are stripped; OCR/typo variants folded
(Thompson→Thomson, Roberson/Roberston→Robertson, "Mady by"→"Made by", "moti�on"→"motion").
The two-line running **page footer** (a lone page-number line + `Nephi City Planning
Commission  <date>`) is removed up front by `FOOTER_RE`/`strip_footers()` so it can't bleed
into a motion whose action prose straddles a page break (fixed 2026-07-19).
**Ann Peterson vs Fran Petersen** share a surname: a bare "Peterson"/"Petersen" is resolved from
the meeting's **attendance header** when exactly one of them is seated (header-based, not a guess);
otherwise left unresolved (dropped) — never guessed. Non-commissioners who appear in attendance
(staff e.g. Seth Atkinson the City Administrator; City Council liaisons e.g. Shari Cowan / Skip
Worwood; the public) are not in the canon and are excluded from movers/seconders/voters/roster.

## ROSTER
`roster.csv` is built from attendance (full-document scan: 2020–2021 + public-hearing minutes put
the roster at the BOTTOM, sometimes as bare names mixed with the public; `normalize_name` keeps only
the 13 canonical commissioners). Excused members are subtracted.

**Appointment cross-check** vs `../meeting_minutes/all_votes.csv` (motion_type=Appointment): the
Council's only recorded PC appointment in range is **2022-11-15** — "ratify the appointment of
**Heather Robertson** as a voting member and **John Ford** as an alternate member of the Planning
Commission" (Pass, unanimous). Both are on `roster.csv` (first seen earlier as attendees/alternates;
ratified as voting member/alternate on that date). Most commissioners predate the 2020 data floor or
were appointed in years the Council minutes don't classify as "Appointment", so the cross-check is
necessarily partial — it confirms (does not enumerate) the roster.

## Coverage (last run)
- **70 meetings parsed · 331 motions · 360 CSV rows · 13 commissioners · 2020–2026.**
- **7 zero-motion meetings** (public hearings / discussion-only — no action taken → no rows).
- Disposition: **95 recommendations · 32 final actions · 204 procedural.**
- **12 motions name individual voters** (41 member-vote rows); the other **319 are narrative
  tally-only** (`names_recorded:false`). **10 contested** motions carry a named dissent —
  overwhelmingly land-use (plats, rezones, site plans), and **Cory Thomson is the most frequent
  dissenter**. Notable named votes: 2023-08-09 rezone 3:1, 2023-09-13 7-Eleven site plan 3:1,
  2024-12-11 & 2024-01-10 chair elections (4:1 / 4:0-with-1-abstention), 2025-09-10 rezone 2:2.
- 1 motion (2025-03-12 #3, minutes) has **no recorded mover** — the source literally reads
  "Chair Commissioner motions" with the name omitted; we leave it blank rather than guess.

## Validation — must pass
`validate_votes.py`: 0 off-roster names (members + movers + seconders); JSON↔CSV motion &
member-row reconcile (zero-motion meetings legitimately contribute no rows); 13-col schema with
`body`/`title` fixed; reports the (expected) narrative/tally-only majority and any mover-less motions.
