# meeting_minutes/ — South Salt Lake City Council (+ RDA) vote pipeline

## The one structural fact that governs this city (REVISED 2026-07-16)
South Salt Lake's minutes publication is label-hostile on BOTH portals. The PMN **"Meeting
Minutes" attachment slot is unreliable**: the short-form labels (`YYYY.M.D RC.pdf` /
`YYYY.M.D WM.pdf`) are very often the **agenda PACKET** (a 20–100 MB PDF headed `REGULAR
MEETING AGENDA`, no roll call), sometimes with the real minutes **appended after the
agenda**, and only sometimes a small standalone minutes PDF. The CivicPlus AgendaCenter's
visible *Minutes* slot serves the packet too — but its hidden **`ArchivedMinutes`
previous-version slot holds genuine recorded minutes** (recovered 2026-07-13, promoted into
this dataset 2026-07-16 — 75 Council + 29 RDA docs, `source=agendacenter`). **The only
reliable test for "is this minutes" — and for body/kind — is CONTENT** (roll-call grammar;
the in-body banner: recovered files labelled "work meeting" were mostly REGULAR-meeting
minutes). Agenda-only meetings are logged as honest gaps; pure-agenda files are **not
retained** (they belong to `packets/`, not here).

- Council = PMN body **1295** → `body=Council`. RDA = PMN body **1296** → `body=RDA`
  (separate meetings, same Wednesday; the RDA board **is** the seven council members).
- Acquisition/harvest tools: `.harvest/harvest_minutes.py` (PMN list → content-detect →
  markdown + retained minutes PDF; `.harvest/build_index.py` writes the index +
  `minutes_unrecovered.csv`) and `../pmn_backfill/promote_to_audited.py` (the audited,
  content-verified 2026-07-16 promotion of the AgendaCenter recoveries).

## Files
- `minutes/<year>/<week-monday>/<date>_<stream>_<kind>.md` — clean markdown, born-digital
  `pdftotext -layout` (no OCR). Each carries a provenance header
  (`source: pmn|agendacenter | body | pmn_file | label | date | meeting_kind | source_url |
  retrieved` — agendacenter rows add `ac_file`/`recovery`/`promoted`).
  Council meets **2nd & 4th Wednesday** (Work 6:30 + Regular 7:00); the folder is keyed on
  that week's Monday. `kind ∈ {RC regular, WM work, SM special, BoC board-of-canvassers,
  TT truth-in-taxation}`.
- `raw/<date>_<stream>_<kind>_<pmnfile>.pdf` (PMN) / `raw/<slug>_<ac_id>.pdf` (AgendaCenter)
  — the retained minutes-bearing source PDF only.
- `minutes_index.csv` — one row per md (`date,year,title,slug,path,source,source_url,format,
  body,meeting_kind,pmn_file`; `source ∈ pmn|agendacenter`, `format=pdf-text`).
- `minutes_unrecovered.csv` — meetings with **no recorded minutes on either portal** (the
  honest gap, never a stub row). Post-promotion residual: 178 Council (117 of them WORK
  meetings) + 19 RDA rows.
- `extract_votes.py` — the PURE deterministic parser (no LLM, no network; resumable).
- `votes/<year>/<week>/<slug>.json` — structured per meeting. `votes/_validation_report.txt`.
- `all_votes.csv` — 13-column standard
  (`date,year,title,body,motion_no,motion,motion_type,result,mover,seconder,member,vote,source`)
  + documented trailing `provenance` column (`minutes` | `agendacenter_minutes`).
- `roster.csv` — the **observed** roster (built by `validate_votes.py`).

## Run
```
python3 extract_votes.py      # writes votes/*.json then rebuilds all_votes.csv
python3 validate_votes.py     # writes votes/_validation_report.txt + roster.csv
```

## Vote grammar — named per-member roll call (max tally 7, Mayor NON-voting)
SSL prints every voter by name (`names_recorded` always True), in one of two shapes:
```
Council Member <X> made a motion to <action>.
MOTION: <Full Name>
SECOND: <Full Name>
Roll Call Vote:              (or "Voice Vote:")
Glad:          Yes
Thomas:        Yes
...
Mitchell:      Not Present
```
`Yes→Aye, No→Nay, Not Present/Absent→Absent, Abstain→Abstain, Recuse→Recuse`. The source
prints **no "motion passed" string**, so `result` is the synthesized tally
`"<aye>-<nay> Pass|Fail"` (no verbatim result exists to preserve); `vote_mode` records
Roll Call vs Voice. Grammar variants handled since 2026-07-16 (all ground-truthed against
source PDFs, zero regressions on the prior corpus): **colon-less rolls** ("Bynum   Yes" —
the 2023–24 RDA clerk and the 2020-09-17 SM); trailing-comma vote lines; scattered
**DRAFT-watermark fragment lines** (D/R/AF/T) stripped so a mid-roll fragment never
truncates the roll; a printed **"None"** value or clerk typo ("Ye", "Y/es") leaves that
member honestly unrecorded without ending the block; 2022-10-26 consent items recorded as
"VOTE: All present in favor" over a blank YES/NO ballot table are captured **tally-only**;
officer elections by acclamation ("no need for a vote") are honestly not motions.
**The Mayor (executive) never appears in a roll call** — the validator
asserts zero mayor-in-roll and zero >7-voter motions. The roster is **OBSERVED per document**
from the `MEMBERS PRESENT` header and evolves 2020→2026 (the 2020 council — Bynum, deWolfe,
Thomas, Huff, Mila, Pinkney, Siwik — is a different seven from 2026 — Glad, Thomas, Bynum,
Mitchell, Jones, Williams, deWolfe); nothing is hardcoded, and a dataset-global surname map
gives RDA/council members consistent full names.

## body column (Council / RDA)
`Council` (RC/WM/SM/BoC/TT) and `RDA`. RDA minutes use the same roll-call grammar (their
header is `MINUTES OF MEETING HELD` + `DIRECTORS PRESENT`); the board is the seven council
members plus the Mayor as non-voting Executive Director. Since the 2026-07-16 promotion the
RDA record is 43 docs / 125 motions (2020→2026); 19 RDA dates remain honestly unrecovered.

## Coverage floor (2020) and the honest gaps
Floor is **2020**. Where NEITHER portal published recorded minutes (PMN minutes slot =
agenda packet; AgendaCenter ArchivedMinutes absent), the meeting is in
`minutes_unrecovered.csv` — post-promotion that residual is **178 Council + 19 RDA** rows,
dominated by council WORK meetings (117), mid-2021→mid-2022 regulars, and the most recent
months. Full story + tables: `../COVERAGE.md`.

## Maintenance notes
- **2026-07-17 — the two clerk-typo vote lines now have documented `db/vote_overrides.csv`
  rows.** `Huff: Ye` (2024-02-28 RDA m2, adjourn) and `Huff: Y/es` (2026-01-14 Council m3)
  are unambiguous typos for `Yes`; the extractor still leaves Huff honestly unrecorded in
  `all_votes.csv` (verbatim source retained), and the override rows document the correction
  (→ `Aye`) with verbatim citations. ✅ **Applied since 2026-07-17 (same day):** the shared
  `db_build_lib.py` gained an **add-member** override kind, so both corrections now land as
  db `vote` rows (the flat CSV stays verbatim-faithful); `h.db` reconciles exactly — see
  `../db/SCHEMA.md`. Unrelated: the 2025-07-23 Council m3 `Y/N` line is a **blank
  ballot template** for the whole roll (genuinely uncaptured, NOT a typo) — no override.
