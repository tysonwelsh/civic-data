# South Salt Lake — minutes & vote coverage (rewritten 2026-07-16 after the ArchivedMinutes promotion)

Minutes + roll-call votes for the **City Council**, **Redevelopment Agency (RDA)**, and
**Planning Commission (PC)**. Two acquisition sources feed one audited layer: the original
**Utah Public Notice (PMN)** harvest (`source=pmn`) and the **2026-07-13/16 CivicPlus
AgendaCenter `ArchivedMinutes` recovery** (`source=agendacenter`, promoted into the audited
layer 2026-07-16 — see `pmn_backfill/` for the recovery provenance). Read `recon.md` and
`meeting_minutes/CLAUDE.md` before any quantitative claim.

## The headline (revised): the cliff was real but HALF the story
The original build was right that SSL's **PMN "Meeting Minutes" slot mostly serves agenda
packets** — that gap is verified and permanent on PMN. But the city's own AgendaCenter hides
genuine recorded roll-call minutes in an **`ArchivedMinutes` previous-version slot** (the
visible *Minutes* slot serves the packet), and for many 2022–2023 PC dates the *Minutes* slot
itself is real minutes. **119 recovered documents (2022–2026) were verified and promoted into
the audited layer on 2026-07-16** (of 130 recovered: 2 were agenda packets mis-detected as
minutes and 9 were content-duplicates of already-audited meetings — never double-ingested).

**Portal labels lie — every promoted doc was re-classified from in-body content**: most
recovered council docs labelled "work meeting" are the 7:00 p.m. REGULAR meeting minutes;
one "RDA" slot doc (2025-02-12) is council minutes; 2024-08-07 is the Truth-in-Taxation
hearing (kind `TT`).

## What is on disk now (audited layer, as of 2026-07-16)

| Body | Files | of which promoted 2026-07-16 | Motions | Coverage span |
|---|---|---|---|---|
| **City Council** | 95 (RC 87 / WM 4 / SM 3 / TT 1) | 75 (2022-09 → 2026-05) | 555 | 2020 → 2026 |
| **RDA** | 43 (all RC) | 29 (2023-01 → 2026-06) | 125 | 2020 → 2026 |
| **Planning Commission** | 60 (PC 54 / WM 6) | 15 (2022-01 → 2026-02) | 286 | **2022** → 2026 |

- `meeting_minutes/all_votes.csv`: **4,606 rows / 680 motions**;
  `planning_commission/all_votes.csv`: **1,652 rows / 286 motions**.
- Every vote row carries the documented trailing **`provenance`** column:
  `minutes` (PMN-harvested audited primary, 374 motions) vs **`agendacenter_minutes`**
  (the promoted recoveries, 592 motions). Filter on it for a pre-recovery cut.
- **PC minutes begin 2022-01-20**, not 2023-01-19 — the 2022 PC minutes were published on
  the AgendaCenter, never on PMN. **2020–2021 PC remains a genuine gap** (the AgendaCenter
  PC listing itself starts 2022).
- The formerly thin mid-2021→2025 council record is now substantially filled: regular-meeting
  minutes exist for most 2022-09 → 2026-06 council Wednesdays.

## The residual (still-honest) gap — 221 agenda-only meetings
`minutes_unrecovered.csv` per dataset, counted from disk 2026-07-17:

| Body | Residual rows | Breakdown |
|---|---|---|
| Council | 178 | RC 54 · **WM 117** · SM 3 · BoC 3 · TT 1 |
| RDA | 19 | RC 19 |
| PC | 24 | WM 14 · PC 10 |
| **Total** | **221** | |

> **PC ledger reconciliation (2026-07-17):** the PC row was **16** on 2026-07-16 (the
> 2026-07-16 table's "17" less the 2024-07-18 no-quorum minutes promoted 2026-07-17). A
> cross-check then found the PC ledger **omitted 8 genuine 2022 agenda-only PC dates**
> (2022-03-03, -03-17, -04-21, -05-05, -06-16, -07-21, -10-20, -12-01) — each a regular PC
> meeting with an AgendaCenter `?packet=true` packet + a PMN "Notice of Planning Commission
> Agenda" but **no minutes on any channel**. They are now logged (PC → 24, total → 221). Four
> other 2022 PMN-only dates were verified and **excluded as non-meetings**: 2022-01-07 &
> 2022-03-04 (public-hearing notices, not PC meetings), 2022-03-11 (the publish date of the
> 03-17 agenda), 2022-06-02 (a **cancelled** meeting) — adding them would fabricate meetings.
> Council/RDA ledgers were cross-checked and need no change.

The dominant residual is **council work-meeting minutes** (the WM slot genuinely goes
unpublished — the recovered "WM" files were almost all mislabelled regular minutes) plus
mid-2021→mid-2022 council regulars and 2020–2021 PC. This is a publication gap at the city,
verified on both PMN and the AgendaCenter, not a scraper miss.

## Vote data — quality
- Named per-member roll calls; **max council/RDA tally = 7** (Mayor is executive, NON-voting —
  validators confirm **0 mayor-in-roll**, **0 >7-voter** motions); PC seats up to 8.
- `result` is the synthesized tally `"<aye>-<nay> Pass|Fail"` (SSL prints no result string);
  `vote_mode` records Roll Call vs Voice vs (PC) Vote. `validate_city.py` f.tally: **100%**
  of synthesized tallies equal the counted member rows (961/961 in motions_std).
- **Contested votes (the signal): 68** (db `v_contested`; Council/RDA 56, PC 12) — up from 12
  pre-promotion. E.g. 2025-07-23 council 6-1 (Sanchez Nay, City-Recorder-fee ordinance);
  2024-02-28 council 6-1 (Sanchez Nay).
- 2026-07-16 extractor extensions (all ground-truthed, zero regressions on the pre-promotion
  corpus): whitespace-separated roll calls (the 2023–24 RDA clerk prints "Bynum   Yes" with no
  colon — also recovered 2 motions/14 votes in the audited 2020-09-17 SM), trailing-comma vote
  lines, scattered DRAFT-watermark fragments stripped, printed "None" votes and clerk-typo
  values ("Ye", "Y/es") skip without truncating the roll (member honestly unrecorded), and
  consent items recorded as "VOTE: All present in favor" captured tally-only.
- **The referral layer is no longer empty: 43 links** (40 Council←RDA, 3 Council←PC, all
  `medium`/subject-match) — the promotion restored the Council side of the record.
- Rosters are **observed** and evolve 2020→2026 (`roster.csv` per dataset); source spelling
  variants are retained faithfully ("Oliva/Olivia Spencer"; "Leanne/LeAnne Huff" in the
  2020-09-17 SM).

## Promotion audit trail
- Recovery dataset + provenance: `pmn_backfill/` (index.csv `recovery_source` column).
- Promotion script (verified classification tables + reject reasons):
  `pmn_backfill/promote_to_audited.py`.
- 11 recovered docs NOT promoted: 2 work-meeting agenda packets (2023-07-26, 2024-07-10 —
  content-detection false positives) and 9 content-duplicates of audited meetings (3 council:
  2025-03-12, 2026-06-10, 2026-06-17; 6 PC: 2023-03-16, 2023-06-01, 2023-09-21, 2024-07-11,
  2025-07-10, 2026-05-07). The 2023-09-21 duplicate contains one extra ADJOURN motion the
  audited PMN copy lacks (page-cut) — logged as a follow-up.
- Backups of every canonical file modified: `_backups/2026-07-16-minutes-promotion/south_salt_lake/`.

## Regenerate
```
python3 fetch_new.py --probe                           # PMN refresh probe (see CLAUDE.md)
cd meeting_minutes      && python3 extract_votes.py && python3 validate_votes.py
cd planning_commission  && python3 extract_votes.py && python3 validate_votes.py
python3 db/build_db.py && python3 db/build_referrals.py && python3 build_weeks.py
python3 ../scripts/normalize_motions.py south_salt_lake
```
