# PMN backfill — coverage cross-check (West Jordan)

**As-of:** 2026-07-03 · **Source:** Utah Public Notice Website (PMN), `https://www.utah.gov/pmn/`
**Bodies cross-checked:** City Council (PMN body id **395**), Planning Commission (PMN body id **396**).
**Method:** per-**DATE** set-difference (not per-year counts), ±4-day tolerance for
meeting-date vs. posted-date offset. Every recovered file was **content-verified** (header
body name + internal "HELD" date + MOTION/vote presence) before inclusion.

PMN's notice *list* view claims "only past 6 months," but the cumulative pager
`/pmn/list/notices.html?id=<body>&page=300` returns the body's **entire** history in one GET:
council notices back to 2012 (1,543 notices), PC back to 2008 (653). We filtered to
attachments labeled `(Meeting Minutes)` for meeting years **2020+** and diffed those dates
against the repo's `minutes_index.csv` dates.

## Column meaning
- **repo** = rows in the existing audited `minutes_index.csv` for that year (the repo can
  hold >1 minutes doc per date — e.g. Work Session + Regular same Tuesday — so this is a row
  count, not a unique-date count).
- **PMN** = distinct PMN notices carrying a `(Meeting Minutes)` attachment that year.
- **recovered** = PMN minutes dates with **no** repo minutes within ±4 days → downloaded here.
- **still-missing** = recovered dates we could not retrieve/verify (0 for both bodies).

PMN attaches minutes sporadically and the repo (PrimeGov API) is generally a **superset** of
PMN for 2023+, so raw counts (repo vs PMN) do **not** measure gaps — only the per-date diff does.

## City Council (body 395)

| Year | repo rows | PMN minutes | recovered | still-missing |
|------|----------:|------------:|----------:|--------------:|
| 2020 | 44 | 31 | 0 | 0 |
| 2021 | 38 | 27 | 0 | 0 |
| 2022 | 56 | 38 | 1 | 0 |
| 2023 | 49 | 40 | 0 | 0 |
| 2024 | 50 | 42 | 2 | 0 |
| 2025 | 58 | 49 | 0 | 0 |
| 2026 | 26 | 22 | 2 | 0 |
| **Total** | **321** | **249** | **5** | **0** |

**Council gaps recovered (5):**
- `2022-01-03` — Oath of Office Ceremony (special ceremonial council meeting; repo has 01-12, 01-26).
- `2024-01-03` — Oath of Office (special ceremonial council meeting; repo starts 01-10).
- `2024-08-13` — Truth in Taxation Hearing. Header reads **Fairway Estates Special Service
  Recreation District Truth in Taxation Hearing** — the council sits as that district; posted
  under the City Council body on PMN. Substantive (adopts the SSD tax rate). Repo has 08-21, 08-27.
- `2026-06-09` — City Council Meeting (regular; 47 motion mentions, full roll-calls). Beyond the
  repo's max council date (2026-05-26).
- `2026-06-09` — Committee of the Whole Meeting (work session, same evening; no formal votes — expected).

## Planning Commission (body 396)

| Year | repo rows | PMN minutes | recovered | still-missing |
|------|----------:|------------:|----------:|--------------:|
| 2020 | 1 | 0 | 0 | 0 |
| 2021 | 2 | 16 | 16 | 0 |
| 2022 | 11 | 22 | 12 | 0 |
| 2023 | 19 | 17 | 0 | 0 |
| 2024 | 20 | 20 | 0 | 0 |
| 2025 | 20 | 20 | 0 | 0 |
| 2026 | 11 | 13 | 0 | 0 |
| **Total** | **84** | **108** | **28** | **0** |

**PC gaps recovered (28)** — the material finding. The repo's PrimeGov feed is nearly empty for
Planning Commission before **mid-2022** (repo held only 2021-03-31, 2021-08-31, then 2022-07-19+).
The parent `CLAUDE.md` states "2020–21 had only joint Council+PC work sessions (no standalone PC
meetings)" — **PMN shows that is not true for 2021**: the Commission held and posted minutes for
regular standalone meetings throughout 2021 and the first half of 2022. Recovered here:

- **2021 (16):** 04-06, 04-20, 05-04, 05-18, 06-01, 06-15, 07-06, 07-20, 08-03, 09-07*, 09-21,
  10-05, 10-19, 11-17, 12-07, 12-21.
- **2022 (12):** 01-18, 02-01, 02-15, 03-01, 03-15, 04-05, 04-19, 05-03*, 05-17*, 06-07*, 06-21*, 07-05*.

`*` = scanned/image PDF, recovered via Tesseract OCR (6 files: 2021-09-07, 2022-05-03, 05-17,
06-07, 06-21, 07-05); all others are born-digital (`pdftotext -layout`). Every one carries the
"WEST JORDAN PLANNING AND ZONING COMMISSION" header with a matching HELD date and motion text.

## Bottom line
- **33 genuine date-level gaps recovered** (5 council + 28 PC), 0 still missing.
- The high-value result is the **2021–early-2022 Planning Commission run** (28 meetings) that the
  PrimeGov-sourced repo never had — it corrects an explicit "no standalone PC meetings in 2021"
  claim in the parent docs.
- Council coverage was already near-complete; the 5 recovered are 2 ceremonial Oaths of Office,
  1 SSD truth-in-taxation hearing, and the June-2026 pair newer than the last repo fetch.
- This is a **separate, un-merged dataset**. It is NOT wired into `all_votes.csv`, `db/`, or
  `weeks/`. Merge deliberately after review (see CLAUDE.md).
