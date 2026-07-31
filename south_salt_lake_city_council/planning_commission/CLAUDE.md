# planning_commission/ — South Salt Lake Planning Commission vote pipeline

Same schema and pipeline as `meeting_minutes/`, for the Planning Commission
(`body=PlanningCommission`). Read `../meeting_minutes/CLAUDE.md` first — the PMN
minutes-slot-serves-agenda caveat and the content-detection harvest apply identically.

## Source & coverage (REVISED 2026-07-16)
- PC = PMN body **1297** (`source=pmn`, recorded minutes `… SSLC PC Mtg_Final.pdf` from
  2023-01-19) **plus the CivicPlus AgendaCenter** (`source=agendacenter`): the 2026-07-16
  promotion added **15 recovered PC minutes 2022-01-20 → 2026-02-05** from the hidden
  `ArchivedMinutes`/`Minutes` slots — **refuting the earlier claim that 2020–2022 PC minutes
  were never published**. Recorded **PC minutes now begin 2022-01-20** (9 regular + 6 work
  meetings recovered; `meeting_kind ∈ PC | WM`). **2020–2021 PC remains a genuine gap** (the
  AgendaCenter PC listing itself starts 2022), plus 24 residual agenda-only dates (8 genuine
  **2022** PC dates added 2026-07-17 after a ledger cross-check + 16 from 2023+) —
  all in `minutes_unrecovered.csv`, not a scraper miss. Promoted vote rows carry
  `provenance=agendacenter_minutes` (trailing 14th all_votes column).
- PC meets **Thursday** (~1st & 3rd); the folder is keyed on that week's Monday.
- ⚠ Some PC minutes PDFs (both PMN `_Final` copies and AgendaCenter recoveries) carry a
  vertical DRAFT watermark that pdftotext scatters as stray letters (D/R/AF/T) — the
  extractor strips them (whole-line, line-leading, and after a `Vote:` header) so they
  never truncate a roll. The watermark appears on `_Final`-labelled approved copies too,
  so it is NOT evidence a doc is an unapproved draft.

## PC vote grammar differs from the council's
PC records a motion as:
```
1.  <Agenda item — application / plat / CUP / rezone …>
Motion to APPROVE <subject>:
Motion:      Commissioner <Name>
Second:      Commissioner <Name>
Vote:        Commissioner <Name> – Aye;
             Commissioner <Name> – Aye;
             ...
             The vote was unanimous.
```
i.e. **`Commissioner <Name> – Aye;`** (role prefix, en-dash, semicolon) rather than the
council's `Surname: Yes`, and a **`Vote:`** header (the first member often sits on the header
line). Some procedural motions (agenda/minutes approval) are recorded as a **tally-only**
`Vote: The motion passed with the unanimous consent of the Commission.` — captured honestly
with `names_recorded:false` and a single placeholder row (no members fabricated). The single
`extract_votes.py` handles both grammars; the PC roster is observed from the PC present-list
(its own commissioners, not the council members). PC → Council recommendation motions
("forward a recommendation of APPROVAL/DENIAL …") are captured verbatim in the motion text.

## Run — identical to meeting_minutes
```
python3 extract_votes.py
python3 validate_votes.py
```
(`extract_votes.py` / `validate_votes.py` here are the same tools, rooted at this dataset.)

## Maintenance notes
- **2026-07-17 — 2024-07-18 NO-QUORUM minutes promoted** (PMN file 1152427, notice
  927292, `071824 SSLC PC Regular Mtg_Final.pdf`). A genuine recorded-minutes doc: header
  + members-present roster (Carter/Slifka/Southey) + "No Planning Commission meeting was
  held because there was not quorum present. All items on the agenda will be re-noticed for
  the next regulated scheduled meeting on August 1, 2024." (that 2024-08-01 meeting is in
  the index — corroborated). Promoted to `minutes/2024/2024-07-15/2024-07-18_pc_PC.md`
  (`source=pmn`, `provenance=minutes`); raw retained. **It has 0 motions BY FACT** — the
  extractor recorded it cleanly as `votes: []` (no fabricated placeholder), so it adds a
  meeting to the index (61 total) and **0 rows** to `all_votes.csv`. Dropped from
  `minutes_unrecovered.csv`. This closes the crosscheck's one standing SSL PC recovery lead.
