# PMN backfill — coverage cross-check (Lehi City Council + Planning Commission)

**As-of:** 2026-07-02 · **Source:** Utah Public Notice Website (PMN), `https://www.utah.gov/pmn/`
**PMN public-body ids:** City Council = **2512**, Planning Commission = **2651**
(also discovered for Lehi: RDA=3315, Local Building Authority=7881, Board of Adjustments=2661,
Appeal Authority=5645, plus several advisory boards — see `CLAUDE.md`).
**Scope:** the repo's data floor is **2020** (`recon.md`); PMN minutes dated before 2020 are
recorded below as context but are **out of scope** and not treated as gaps.

## Bottom line

**The repo's audited `meeting_minutes/` + `planning_commission/` layers (built from Granicus)
are the SUPERSET.** For 2020–present, the repo holds **more** approved minutes than PMN carries
in almost every year — PMN attaches minutes to its meeting-agenda notices only sporadically.
A per-**date** set-difference (not a raw count comparison) found exactly **6** meeting dates in
the 2020–present window that PMN has minutes for and the repo lacked. **All 6 have been recovered**
into `raw/` + `text/` + `index.csv`. After recovery, **0 in-scope PMN minutes remain unrecovered.**

Two numbers matter and they are different:
- **Per-year counts** (below) show the repo ≥ PMN every in-scope year — PMN minutes attachments
  are sparse, so year counts *understate* PMN and are NOT the gap signal.
- **Per-date set difference** is the real test: which specific meeting dates does PMN carry that
  the repo does not? That produced the 6 recovered items in `index.csv`.

## How PMN was enumerated (GET-only, polite)

PMN's public **search** (the only UI path to notices older than the recent window) is a
**POST** endpoint (`/pmn/searchresult.html`, CSRF-protected) — disallowed by the polite-scraper
rule and not supported by `polite_fetch.py`. Instead, the site's **GET** browse endpoint
`/pmn/list/notices.html?id=<bodyId>&page=<N>` was used. `page` is **cumulative** (each increment
appends ~5 older notices and re-returns the whole list from newest), so a single high page number
returns the body's **entire** notice history. Saturation:
- Council 2512 → **981 notices**, 2009-10-27 … 2026-06-09 (page 200 = full).
- PC 2651 → **565 notices**, 2010-02-04 … 2026-07-09 (page 200 = full).

Each notice row exposes its attachments with a **type label**; minutes carry `(Meeting Minutes)`.
Full-history counts of `Meeting Minutes` attachments: council **252**, PC **30**.

## City Council (body 2512)

| Year | Repo minutes | PMN notices w/ minutes attached | Per-date gaps repo lacked (recovered) |
|------|-------------:|--------------------------------:|:--------------------------------------|
| 2020 | 25 | 25 | 2 (02-04 Work Session; 08-04 Joint Work Session) |
| 2021 | 26 | 13 | 1 (07-13 Regular Meeting) |
| 2022 | 31 | 17 | 0 |
| 2023 | 30 | 26 | 0 |
| 2024 | 33 | 21 | 0 |
| 2025 | 27 | 20 | 0 |
| 2026 | 3  | 3  | 0 |
| **Total (2020+)** | **175** | **125** | **3 recovered** |
| pre-2020 (out of scope) | 0 | 127 | — |

## Planning Commission (body 2651)

| Year | Repo minutes | PMN notices w/ minutes attached | Per-date gaps repo lacked (recovered) |
|------|-------------:|--------------------------------:|:--------------------------------------|
| 2020 | 28 | 0  | 0 |
| 2021 | 24 | 0  | 0 |
| 2022 | 28 | 0  | 0 |
| 2023 | 26 | 0  | 0 |
| 2024 | 23 | 2  | 0 |
| 2025 | 21 | 18 | 3 (03-06, 08-07, 09-04 — all Work Sessions) |
| 2026 | 10 | 0  | 0 |
| **Total (2020+)** | **160** | **20** | **3 recovered** |
| pre-2020 (out of scope) | 0 | 10 | — |

> **2026-07-02 note:** "Repo minutes" counts updated after the duplicate-Granicus-event dedup
> (6 council + 2 PC same-date duplicate files removed — see `../VERIFICATION.md` addendum). The
> per-**date** set-difference above is unaffected: every deduped date retains its kept file, so
> the recovery conclusions (6 dates, all recovered) stand unchanged.

PC barely uses PMN minutes attachments before 2025 (0 in 2020–2023, 2 in 2024). The repo's PC
minutes (from Granicus) fully cover those years; PMN adds nothing there. In 2025 PMN began
attaching PC minutes, surfacing the 3 first-Thursday work sessions the Granicus-built repo lacked.

## Recovered items (see `index.csv`)

| date | body | title | PMN file | notice |
|------|------|-------|---------:|-------:|
| 2020-02-04 | Council | Work Session | 579985 | 585247 |
| 2020-08-04 | Council | Council + Planning Commission Joint Work Session | 648415 | 619919 |
| 2021-07-13 | Council | Pre Council + Regular Session (2nd-Tuesday regular meeting) | 744781 | 689345 |
| 2025-03-06 | PC | Work Session | 1360049 | 978241 |
| 2025-08-07 | PC | Work Session | 1360131 | 1013783 |
| 2025-09-04 | PC | Work Session | 1360147 | 1020005 |

All 6 are **born-digital** minutes PDFs (clean `pdftotext -layout`; corpus screener clean). The
2021-07-13 item is the most substantive — a full regular council meeting the repo was missing;
the others are work/joint sessions Granicus did not carry minutes for.

## What remains genuinely missing / out of scope

- **Nothing in-scope remains unrecovered.** Every PMN meeting-minutes attachment dated 2020-01-01
  or later that the repo lacked is now in `index.csv`.
- **Pre-2020 PMN minutes (127 council, 10 PC)** are deliberately NOT recovered — below the repo's
  2020 data floor. They are enumerated in `raw/_notices_2512_p200.html` / `_notices_2651_p200.html`
  and could be harvested later if the floor is lowered (file ids are in `council.json` / `pc.json`).
- **RDA (3315), LBA (7881), Board of Adjustments (2661)** were not cross-checked here (task scoped
  to council + PC). The repo's `meeting_minutes` already carries LBA (`body=MBA`, 9 rows).
