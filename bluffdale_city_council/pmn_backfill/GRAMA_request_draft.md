# Drafted GRAMA request — Bluffdale unrecovered Council minutes (2026-07-17)

Two Bluffdale City Council meetings are confirmed to have been HELD and to have had
minutes formally approved by the Council, yet the approved minutes were never published
on any sanctioned channel (the CivicPlus/CivicEngage AgendaCenter carries only the
Agenda for each; Utah Public Notice carries agenda + packet only; there is no CivicPlus
ArchiveCenter and the PreviousVersions slot for each item exposes only the Agenda
version). They are logged in `meeting_minutes/minutes_unrecovered.csv`. A GRAMA request
is the remaining recovery path.

| meeting date | body | approved at | portal evidence | PMN notice |
|---|---|---|---|---|
| 2022-08-16 | City Council, LBA & RDA (combined) | 2022-09-14 Council mtg, consent item 2.1 | AgendaCenter Agenda docids 1100 / 1101 (both amended-agenda items); Minutes ViewFile 404 | 774853 |
| 2026-02-11 | City Council & RDA | 2026-02-25 Council mtg, consent item 2.1 | AgendaCenter Agenda docid 1761; Minutes ViewFile 404 | 1057937 |

---

## Draft request text (ready to send)

> To: Bluffdale City Recorder / GRAMA Officer (recorder@bluffdale.gov)
> Subject: GRAMA request — approved minutes for two City Council meetings
>
> Pursuant to the Utah Government Records Access and Management Act (Utah Code
> §63G-2-201 et seq.), I request a copy of the **approved minutes** for the following two
> Bluffdale City Council meetings. Public records show both meetings were held and their
> minutes were approved by the Council, but the approved minutes are not posted on the
> City's AgendaCenter (only the meeting agendas appear there).
>
> 1. **August 16, 2022** — Bluffdale City Council, Local Building Authority & Redevelopment
>    Agency Combined Meeting. (Minutes approved as consent item 2.1 at the September 14,
>    2022 City Council meeting.)
> 2. **February 11, 2026** — Bluffdale City Council & Redevelopment Agency Board Meeting.
>    (Minutes approved as consent item 2.1 at the February 25, 2026 City Council meeting.)
>
> I request the records in electronic form (searchable PDF preferred). If any portion is
> claimed exempt, please cite the specific statutory basis and release the remainder. I am
> a member of the public requesting these for research/non-commercial use and request a fee
> waiver as the records serve the public interest; if fees are unavoidable, please provide
> an estimate before proceeding.
>
> Thank you.

## Status

Not yet sent (drafting only, per task scope). If sent and fulfilled, ingest the returned
PDFs through the normal channel: `raw/` → markdown (OCR-aware header per `convert_minutes.py`)
→ `minutes_index.csv` with an honest `provenance`/source label, then re-run `extract_votes.py`,
rebuild db + weeks, and move the corresponding row(s) out of `minutes_unrecovered.csv`.
Vote-extraction quirks for these meetings: 5 at-large Council seats (roll caps at 5; Mayor
tie-break only); the in-session **RDA/LBA** portions have the **Mayor voting as Chair** (rolls
of 6). The 2026-02-11 combined CC/RDA doc will fall in the 2023–2026 partial-OCR seam.
