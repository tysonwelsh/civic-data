# Ogden PMN backfill — coverage (as-of 2026-07-05)

Additive PMN backfill of meeting minutes MISSING from the audited `meeting_minutes/`
(and `planning_commission/`) layers. Scope window **2020–2026**. Set-difference is keyed
on `(body, meeting-date)` with a ±4-day tolerance; PMN meeting date read from each
attachment filename and re-confirmed inside every recovered PDF.

## Minutes present on PMN by body × year vs. repo (target-window bodies)

Legend: **repo** = count already in the audited layer; **PMN** = distinct minutes on PMN;
**+new** = recovered here (net-new, additive).

| Body | Year | repo | PMN minutes | +new recovered |
|------|------|-----:|-----:|-----:|
| **RDA** | 2020 | 0 | 0 | 0 |
| **RDA** | 2021 | 0 | 0 | 0 |
| **RDA** | **2022** | **0** | **0 (not on PMN)** | **0** |
| **RDA** | **2023** | **0** | **7** | **7** ✅ |
| **RDA** | 2024 | 14 | ≥15 | 1 (2024-04-23) |
| **RDA** | 2025 | 11 | — | 0 |
| **MBA** | **2020** | 0 | 2 | **2** |
| **MBA** | 2021 | 0 | 0 | 0 |
| **MBA** | **2022** | **0** | **0 (not on PMN)** | **0** |
| **MBA** | **2023** | **0** | **0 (not on PMN)** | **0** |
| **MBA** | 2024 | 3 | — | 0 |
| **MBA** | 2025 | 3 | — | 0 |
| CC (Council/WS) | 2020–2026 | full | present | 0 (no in-window gaps) |
| PC | 2020–2026 | full | present | 0 (no in-window gaps) |

## >>> TARGET GAP: 2022–2023 RDA & MBA minutes <<<

The known repo gap is RDA/MBA minutes for 2022–2023 (never acquired). PMN result:

- **2023 RDA — 7 minutes RECOVERED** (Jan 17, Jun 6, Jul 11, Aug 15, Oct 10, Nov 7,
  Nov 28) — net-new, flagged for promotion review.
- **2022 RDA — 0 recoverable.** PMN carries only RDA budget/hearing *notices* for 2022,
  no minutes attachment. HONEST GAP (source published no 2022 RDA minutes to PMN).
- **2022 MBA — 0 recoverable.** Same (budget adoption notices only).
- **2023 MBA — 0 recoverable.** Same (bond/pledge/hearing notices only).

So the 2022–2023 RDA/MBA target yields **7 recovered RDA minutes (all 2023)**; the 2022
RDA/MBA and 2023 MBA minutes are simply not on PMN — recorded as gaps, not fabricated.

## Bonus net-new outside the target but in-window
- **2020 MBA — 2 minutes** (May 12, Jun 9) recovered.
- **2024-04-23 RDA** — 1 minutes recovered (fills the repo's Mar 12 → May 7 RDA gap).

## Totals
- **10 minutes recovered**, 1.68 MB raw PDF, all HTTP 200, all `format=text`
  (`pdftotext -layout`, no OCR needed).
- **7 of the 10 are the 2022–2023 RDA/MBA target-gap recovery** (all 2023 RDA).
- 0 in-window City-Council or Planning-Commission dates missing — those layers are
  complete for 2020–2026.

All 10 rows carry `status=recovered` and are **net-new RDA/MBA minutes → flag for
promotion review** into the audited `meeting_minutes/` layer (with `body` populated).
