# SLC PMN backfill — coverage

**As-of:** 2026-07-05 · scope 2020–2026 · counts = PMN notices carrying a `(Meeting
Minutes)` attachment, per year, per body. "Recovered" = added to this dataset because the
audited minutes layer lacked it.

## PMN minutes-attachment notices by body × year (in scope)

| Body (PMN id) | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 | In-scope recoveries |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Salt Lake City Council (1360) | 67 | 63 | 64 | 69 | 58 | 60 | 12 | **7** |
| Planning Commission (1274) | 0 | 0 | 0 | 8 | 11 | 20 | 3 | 0 |
| Redevelopment Agency / RDA (1277) | 11 | 15 | 17 | 17 | 18 | 0 | 0 | 0 |
| Community Reinvestment Agency / CRA (9033) | 0 | 0 | 0 | 0 | 0 | 19 | 3 | 0 |
| Local Building Authority / LBA (3475) | 5 | 5 | 5 | 4 | 4 | 5 | 0 | 0 |

RDA/CRA/LBA minutes dates are a subset of the Council series (SLC reconvenes in-session as
those bodies inside one combined minutes doc), so none are independently recoverable. PC on
PMN only starts 2023 and every date already exists in `planning_commission/minutes_index.csv`.

## The 7 recovered council minutes (→ `index.csv`, `text/`, `raw/`)

| Date | Meeting | PMN file | Words | Why it was missing |
|---|---|---|---:|---|
| 2020-06-09 | Formal Meeting | 645587 | 2,923 | repo held only the 06-09 Work Session |
| 2020-06-16 | Formal Meeting | 645589 | 3,136 | repo held only the 06-16 Work Session |
| 2021-09-14 | Work Session | 908247 | 3,043 | repo has 09-07 & 09-21 only |
| 2021-09-14 | Formal Meeting | 803219 | 699 | repo has 09-07 & 09-21 only |
| 2022-08-29 | Special Limited Formal (Truth-in-Taxation) | 913093 | 1,841 | repo has 08-16 only |
| 2024-01-02 | Oath of Office Ceremony (Formal) | 1089005 | 399 | repo year starts 01-09 |
| 2026-01-05 | Oath of Office Ceremony | 1394079 | 395 | repo year starts 01-13 |

All 7 are born-digital `pdftotext -layout` extractions (`format=text`), screener-clean.
Note: these dates also appear in `meeting_minutes/index_laserfiche.csv` (the raw Laserfiche
*harvest* listing) but their text was never fetched into the corpus — so they are genuinely
absent from the audited `minutes_index.csv` and from disk. PMN supplies the actual text.

## Secondary deliverable — 2020 source-URL recovery (→ `url_recovery_2020.csv`)

The 68 Laserfiche-origin 2020 council minutes rows have **no `source_url`** in the audited
index. This dataset supplies a citable PMN `/pmn/files/<id>.pdf` URL for them:

| Outcome | Rows |
|---|---:|
| Repo 2020 minutes given a recovered PMN URL (exact date + session verified) | **65** |
| Repo 2020 Formal minutes with **no PMN source** (PMN posted WS only: 01-07, 01-17, 01-21) | 3 |
| PMN 2020 "Meeting Minutes" attachment that was actually the **agenda** (excluded) | 1 (file 593695) |
| **Total 2020 repo rows accounted for** | **68** |

Match quality: for all 68 downloaded 2020 PMN minutes PDFs, the meeting date printed inside
the document equalled the PMN notice date exactly (0-day), and the session type (Work
Session vs Formal) was confirmed from the PDF header and the SLC filename convention
(`…ws.pdf` = work session, `…r.pdf` = formal). Confidence = **high** on every matched row.
