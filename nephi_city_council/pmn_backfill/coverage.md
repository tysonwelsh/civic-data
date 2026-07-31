# PMN backfill — coverage cross-check (Nephi City Council + Planning Commission)

**As-of:** 2026-07-05 · **Source:** Utah Public Notice Website (PMN), `https://www.utah.gov/pmn/`
**PMN entity id:** Nephi = **216** · **Public-body ids:** City Council = **1788**,
Planning Commission = **1869** (also present: CRA=5737, LBA=6527, Public Library=1868 —
not cross-checked; the repo has no RDA/CRA body).
**Scope:** the repo's data floor is **2020**; PMN minutes dated before 2020 are recorded
as context but are out of scope and NOT treated as gaps.

## Bottom line

PMN carried **9 in-scope council/PC meeting dates** (2020–2026) that the audited
`meeting_minutes/` + `planning_commission/` layers (built from CivicPlus) lacked — **8
City Council + 1 Planning Commission**. **All 9 were recovered** (`raw/` + `text/` +
`index.csv`, ~2.3 MB PDF, all born-digital text, no OCR). **0 attachments were purged
(404); 0 remain unrecovered.**

Unlike most cities where the repo is a clean superset of PMN, Nephi's audited layer has
**real holes in late-2025/early-2026** (council minutes jump 2025-10-14 → 2025-11-18, and
early-2026 is sparse) plus a missing **2021-08-11** PC meeting — PMN filled all of them.

Two numbers matter and differ:
- **Per-year counts** (below) show the repo ≥ PMN in every year through 2024 (PMN attaches
  minutes only sporadically, so year counts *understate* PMN and are not the gap signal).
  In 2025–2026 PMN's minutes attachments densify and expose the repo's gaps.
- **Per-date set difference** (tolerance ±4 days, on the date printed *inside* each PDF) is
  the real test → the 9 recovered items in `index.csv`.

## How PMN was enumerated (GET-only, polite)

PMN's public **search** is a **POST** endpoint (`/pmn/searchresult.html`, CSRF-protected) —
disallowed by the polite-scraper rule. Instead the **GET** cumulative browse endpoint
`/pmn/list/notices.html?id=<bodyId>&page=300` was used; `page` is cumulative, so one high
page returns the body's entire history:
- Council 1788 → **1,242 notices**, **89** with a `(Meeting Minutes)` attachment.
- PC 1869 → **270 notices**, **22** minutes attachments (20 minutes-bearing notices).

## City Council (body 1788)

Per-year: repo minutes vs PMN notices carrying a minutes attachment (all years), and the
2020+ gap resolution.

| year | repo minutes | PMN notices w/ minutes | recovered | still-missing | 404-purged |
|------|-------------|------------------------|-----------|---------------|-----------|
| 2020 | 43 | 0 | 0 | 0 | 0 |
| 2021 | 47 | 0 | 0 | 0 | 0 |
| 2022 | 38 | 0 | 0 | 0 | 0 |
| 2023 | 36 | 0 | 0 | 0 | 0 |
| 2024 | 35 | 0 | 0 | 0 | 0 |
| 2025 | 35 | 27 | 1 | 0 | 0 |
| 2026 | 9  | 15 | 7 | 0 | 0 |
| **pre-2020** | — | 47 | 0 (out of scope) | — | 0 |

Recovered council dates (meeting date read inside PDF; notice date in parentheses):
- **2025-10-21** regular  (notice 2025-11-04, file 1346003)
- **2026-01-06** regular  (notice 2026-01-06, file 1380339)
- **2026-01-13** work session (file 1380355)
- **2026-02-03** regular  (notice titled "Agenda"; file 1393289 is minutes)
- **2026-02-10** work session (notice titled "Agenda"; file 1393295 is minutes)
- **2026-03-24** work session (file 1419795)
- **2026-04-07** regular  (file 1428903)
- **2026-04-14** work session (file 1428905)

## Planning Commission (body 1869)

| year | repo minutes | PMN notices w/ minutes | recovered | still-missing | 404-purged |
|------|-------------|------------------------|-----------|---------------|-----------|
| 2020 | 8  | 0 | 0 | 0 | 0 |
| 2021 | 8  | 1 | 1 | 0 | 0 |
| 2022 | 17 | 1 | 0 | 0 | 0 |
| 2023 | 13 | 0 | 0 | 0 | 0 |
| 2024 | 11 | 3 | 0 | 0 | 0 |
| 2025 | 11 | 8 | 0 | 0 | 0 |
| 2026 | 2  | 1 | 0 | 0 | 0 |
| **pre-2020** | — | 6 | 0 (out of scope) | — | 0 |

Recovered PC date:
- **2021-08-11** regular (file 770863) — zone-change hearing, North Ridge Subdivision Phase B.

The 2022/2024/2025/2026 PMN minutes attachments all fell within ±4 days of a minutes
document the repo already holds → not gaps (`status` not in index; duplicates were
confirmed by the set-difference, none required downloading).

## Totals

- **Recovered:** 9 (8 council + 1 PC) · **~2.3 MB** raw PDF · all `format=text`.
- **404-purged / source-unavailable:** 0.
- **Still-missing after recovery:** 0 (in scope).
