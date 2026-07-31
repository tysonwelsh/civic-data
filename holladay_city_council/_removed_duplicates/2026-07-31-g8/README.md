# Removed duplicate — Council "2025-05-01" (PMN file 1282121)

**Date removed:** 2026-07-31 (duplicate-ingest collision wave, group g8)

## What was wrong
`minutes_index.csv` carried a Council row for **2025-05-01** pointing at PMN file
`1282121`. That PDF is **byte-identical** (md5 `45c7445e1d5384c760dc78fdf3f06d49`) to PMN
file `1282125`, the **2025-05-15** Council minutes — so the same meeting was ingested
twice under two dates and its 3 motions double-counted.

## Evidence (verified at source, live 2026-07-31)
1. **In-body date.** The document's own caption reads `Thursday, May 15, 2025` and every
   page footer reads `Holladay City Council Work Meeting Minutes 05/15/25`. Nothing in it
   refers to May 1.
2. **Byte identity.** `curl https://www.utah.gov/pmn/files/1282121.pdf` returns md5
   `45c7445e1d5384c760dc78fdf3f06d49` — identical to the stored `1282125` raw.
3. **PMN attachment filename.** On PMN body 388's cumulative notice list
   (`/pmn/list/notices.html?id=388&page=300`), notice **990511** (event date 2025-05-01)
   carries a *Meeting Minutes* attachment literally named **`051525 CC Mtg.pdf`**
   (file 1282121), while notice **994113** (2025-05-15) carries `051525 CC Mtg.pdf`
   (file 1282125). The city uploaded the May-15 minutes to the May-1 notice — an
   **upstream publisher upload error**, the same defect class already logged for PC
   2020-04-07 in `pmn_backfill/unrecovered.csv`.
4. **Approval reference.** The 2025-06-05 Council minutes approve
   "Minutes – April 17, May 1, 8, and 15, 2025" — four distinct meetings, so **2025-05-01
   was a real, separate meeting** and 2025-05-15 is not a re-post of it.

## What replaced it
The **true 2025-05-01 minutes** were recovered from the city's SuiteOne portal
(`https://holladayut.suiteonemedia.com/event/GetMinutesFile/Minutes?mid=1156`, event 2903 —
the same event whose agenda packet is already in `packets/`) and ingested as
`meeting_minutes/minutes/2025/2025-04-28/2025-05-01_city-council-meeting_suiteone1156.md`
(`source=suiteone`). That document's own caption reads `Thursday, May 1, 2025, 6:00 p.m.`
with `Drew Quinn- excused` — a genuinely different meeting.

Files here are retained, never deleted (SCHEMA_SPEC: raw originals are kept).
