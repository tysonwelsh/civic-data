# meeting_minutes/ — Nephi City Council vote extraction

Turns 243 council-minutes markdown files (2020–2026) into structured motion data.
Entry point: **`extract_votes.py`**.

## What's here
| Path | Role |
|------|------|
| `minutes/<year>/<week-monday>/<date>_<slug>.md` | Source minutes (CivicPlus AgendaCenter → markdown; born-digital text PDFs + 17 .docx; the 2021-02-23 work session is re-sourced from Utah PMN — see `source`/`source_url` in the index). Immutable input. |
| `minutes_index.csv` | Index of the 243 files (`date,year,title,slug,path,source,source_url,format`). |
| `extract_votes.py` | Parser → per-meeting JSON + `all_votes.csv`. |
| `votes/<year>/<week>/<date>_<slug>.json` | Structured intermediate, one per meeting. |
| `all_votes.csv` | Long format, one row per motion (or member-vote where named). Authoritative analysis table. |

## Run
```bash
python3 meeting_minutes/extract_votes.py
```

## Nephi specifics — narrative votes, NOT a roll-call grid
Nephi's minutes record motions as prose: `Councilor <X> moved to <…>. Councilor <Y> seconded.
The motion passed unanimously.` **There is no per-member Aye/Nay roll-call grid on routine
business.** Consequences:
- **Every motion captures `mover` + `seconder` + `result` + `motion` + `motion_type`** (all 1,090
  rows carry a mover).
- **Most motions are tally-only** → `names_recorded:false`, with empty `aye`/`nay` lists (we never
  guess who voted which way from a "passed unanimously"). Only **46 of 918 motions** name
  individual voters/dissenters; those set `names_recorded:true`.
- Named **dissents** are captured when the narrative states them ("Councilor X opposed", "X and Y
  voted nay") — across line wraps and comma/"and"-separated lists.
- **Mayor does NOT vote** except to break a tie (`mayor_vote` flag); confirm via the per-year roster.
  Two distinct **Worwood**s in the record — *Skip F. Worwood* (council 2021) vs *Travis L. Worwood*
  (council 2023) — are kept separate.

### `body` column
`body ∈ {Council, CRA}`. Default `Council`. The **2021-07-27** meeting (council sitting as the
**Community Reinvestment Agency**) and any in-meeting "convene as the CRA" recess → `body=CRA`.
Nephi has no separate Redevelopment Agency. (Currently Council 1,089 rows / CRA 1.)

## Coverage (last run)
- **252 meetings · 989 motions · 1,180 rows · 22 contested · 2020–2026.**
- Body: Council 988 · CRA 1. Named roll-calls: 51; the rest are narrative tally-only.
- **~97% of motions pass with no recorded dissent** — the highest consensus rate of any city in
  the collection (a small rural council that moves most business by unanimous voice).


## 2026-07-20 — extractor grammar/name-typo recovery (+57 motions)
Closed two systematic extraction gaps (backups: `_backups/2026-07-19-pv-tierb-low/p4-nephi/`):
1. **`ANCHOR_RE` motion verb** — the 2025+ recorder writes "made **the** motion to …"; the
   anchor only matched `moved` / `made a motion`, so ~40 real motions (all 2025) were dropped.
   Widened to `made\s+(?:a|the)\s+motion` (the `\s+` also catches line-wrapped "made a\nmotion").
2. **Garbled/first-name movers** — added surname aliases so anchors that already existed but
   resolved to no member now emit: `Wowood`→Worwood (the **06-20-2023** ordinance-rescission
   motion), `Pardy`→Parady, `Cown`→Cowan, `Ost.er`→Ostler (internal-period collapse at final
   lookup only — never for Worwood detection, so a spurious "…Riley Worwood. Councilor Ostler"
   span still falls through to Ostler), first-name `Jeramie`→Callaway.

Proven additions-only: of the whole corpus, **exactly one pre-existing row changed** — the
2023-09-19 CR-Circle-3 seconder `''`→`JD Parady` (a genuine recovery; source reads "Councilor
Pardy seconded") — every other delta is a net-new recovered motion or in-meeting renumbering.
918→989 motions, 1,090→1,180 rows, 46→51 named. Recovered the two target land-use ordinance
adoptions (05-20-2025 zone change 4-0; 06-20-2023 rescission) flagged in `ordinances/AVAILABILITY.md`.

## 2026-07-17 — PMN crosscheck promotion (+8 meetings)
Promoted 8 PMN-recovered council minutes (2020-11-24, 2021-10-12, 2022-02-22, 2022-04-26,
2022-07-26, 2023-03-07, 2024-06-25, 2025-10-21) → 243→251 meetings, all_votes 1090→1104 rows,
918→932 motions (named still 46). source=pmn/format=text; raw+text in `pmn_backfill/`.
Two of them (2020-11-24, 2021-10-12) are tour/discussion work sessions with no motion (0 rows).
