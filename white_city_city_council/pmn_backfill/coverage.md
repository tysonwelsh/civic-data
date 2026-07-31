# White City — PMN backfill coverage

As-of **2026-07-13**. Source: Utah Public Notice (`utah.gov/pmn`). Two White City public
bodies under PMN entity **1325**:

| PMN body | id | role |
|---|---|---|
| White City Council | **5805** | council/special/canvass minutes (cross-check of the Streamline layer) |
| White City Planning Commission | **5879** | **the PC minutes series — absent from the core repo, recovered here** |

(Decoy excluded: White City Water Improvement District = PMN entity **840**, govType 5 —
a different special district. The Greater SL Municipal Services District, entity **1345**,
staffs White City planning but hosts no White-City PC minutes body of its own.)

## (a) Council body 5805 — cross-check vs the audited `meeting_minutes/` layer

Method: per-DATE set-difference of PMN "Meeting Minutes" attachments (meeting date parsed
from the filename, not the notice/event date) against `meeting_minutes/minutes_index.csv`.
The repo (Streamline) is the primary layer; PMN is mostly a subset. 102 PMN council minutes
dates already matched the repo.

| Year | repo minutes | PMN min. attachments | recovered here | purged/unrecoverable |
|---|---|---|---|---|
| 2017 | 0 | 19 | 0 | **18** |
| 2018 | 12 | 14 | 0 | 2 |
| 2019 | 14 | 15 | **1** | 0 |
| 2020 | 13 | 13 | 0 | 0 |
| 2021 | 13 | 13 | 0 | 0 |
| 2022 | 16 | 18 | **2** | 0 |
| 2023 | 15 | 19 | **2** | 0 |
| 2024 | 14 | 9 | 0 | 0 |
| 2025 | 14 | 8 | 0 | 0 |
| 2026 | 6 | 3 | 0 | 0 |

**Council recovered (5 meetings, all genuine gaps in the repo, all born-digital
narrative-tally minutes — "…METRO TOWNSHIP MET ON…"):**
`2019-11-14`, `2022-03-03`, `2022-08-18`, `2023-10-05`, `2023-11-02`.

**Council still-missing (20, `unrecovered.csv`):** the full **2017** council year (18
meetings) plus **2018-02-01** and **2018-09-06**. PMN carries a "Meeting Minutes"
attachment for each, but every file **404s** — the pre-~2019 PMN blob purge that also hit
kearns/magna/copperton. Streamline holds only the **agenda** for the 2017 dates. The
notices themselves are the proof these meetings occurred; the minutes documents are gone.
(The core `meeting_minutes/minutes_unrecovered.csv` logged 5 of these 2017 dates as
agenda-only; PMN confirms ~18 council meetings happened in 2017.)

**Note — not acted on here (additive-only rule):** the 2024-09-05 → 2025-01-02 council
minutes that the repo carries as **OCR scans** (`format=ocr`) also exist on PMN as
**born-digital** copies filed under the "Public Information Handout" label
(files 1232445/1232447/1232449/1232451/1232453). A future remediation could upgrade those
5 OCR rows to born-digital text — flagged, not applied (this dataset never edits the
audited layer).

## (b) Planning Commission body 5879 — the headline

The core `planning_commission/` dataset is **honestly empty** (header-only) — White City's
own PC publishes no minutes on its Streamline page, and the earlier recon concluded "no
separate White City Planning Commission publicbody surfaced." **That conclusion was
incomplete: PMN body 5879 exists and carries a real PC minutes series.** All PC minutes
here are net-new (the core PC dataset had zero).

- **22 PC meeting-minutes documents recovered** (2019-01-29 → 2025-05-20), each a genuine
  minutes file with motion grammar (3–21 motions apiece), on Greater SL MSD
  "Planning and Development Services" letterhead (the PC is MSD-staffed). Distribution:
  2019×5, 2020×2, 2021×5, 2022×2, 2023×2, 2024×4, 2025×2.
- **4 General Plan Steering Committee (GPSC) meeting reports** recovered (2021-02-09,
  02-23, 03-09, 03-23) — a distinct General-Plan drafting sub-body (narrative summaries, no
  roll-call motions), indexed `body=GPSC`, that fed the April-2022 General Plan.
- One recovered date (`2019-11-04`) was previously logged in the core
  `planning_commission/minutes_unrecovered.csv` as "packet/agenda only, minutes never
  published" — **now recovered as actual approved minutes.**

**Still-missing PC:** the PC minutes series is **sporadic**, not complete. PMN body 5879
holds 176 notices (2017–2026: 14/20/27/29/22/18/13/13/12/8 per year) — overwhelmingly
agendas/packets ("Other" label) with **no minutes attachment**. Only 22 meetings have a
recoverable minutes document; the PC met ~monthly (4th Thursday) across ~7 years, so the
majority of PC meetings' minutes were **never posted** (agenda-only) — an honest publishing
gap, not a scraper miss. No PC minutes were found on the Streamline `/meetings-archive`
(agendas/packets only) or on the MSD site.

## Formats
30 of 31 recovered docs are **born-digital** (`pdftotext -layout`). One GPSC report
(2021-02-23, file 690347) had a **corrupt embedded text layer** (garbled) and was recovered
by **OCR** (tesseract) — labeled `format=scanned`, `extraction_method=ocr …` in `index.csv`.
