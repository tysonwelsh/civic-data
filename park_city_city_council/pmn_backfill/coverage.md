# PMN backfill — coverage cross-check (Park City Council + Planning Commission + RDA)

**As-of:** 2026-07-05 · **Source:** Utah Public Notice Website (PMN), `https://www.utah.gov/pmn/`
**Park City PMN entity id = 233** (government type 3 = Municipality).
**PMN public-body ids (CONFIRMED):** City Council = **653**, Planning Commission = **1860**,
Redevelopment Agency = **654**, Housing Authority = 657, Municipal Building Authority = 655,
Historic Preservation Board = 659, Board of Adjustment = 4645 (full list in `AVAILABILITY.md`).
**Scope:** repo data floor = **2020** (`../recon.md`); PMN minutes dated before 2020 are recorded
as context but are out of scope and not treated as gaps.

## Bottom line

**The repo's audited `meeting_minutes/` + `planning_commission/` layers (built from CivicClerk)
are the SUPERSET for 2020–present.** A per-**date** set difference (not a raw count comparison)
across all three PMN bodies found:

| Body (PMN id) | In-scope PMN minutes | Per-date gaps repo lacked | Recovered net-new | Duplicates |
|---|---:|---:|---:|---:|
| City Council (653) | 232 | 2 | **2** | 0 |
| Planning Commission (1860) | 43 | 0 | 0 | 0 |
| Redevelopment Agency (654) | 14 | 0 net-new | 0 | 14 |
| **Total** | **289** | **2** | **2** | **14** |

- **2 genuinely net-new City Council minutes** recovered: **2026-06-04** and **2026-06-11**
  regular meetings — both newer than the repo's last CivicClerk council minutes (2026-05-22).
  Fetched, extracted (born-digital, screener-clean), indexed `status=recovered`.
- **Planning Commission: 0 gaps.** The CivicClerk-built PC layer fully covers every PMN PC
  minutes date in scope.
- **Redevelopment Agency (654): 0 standalone RDA minutes exist.** See the RDA section below —
  this is the key finding. All 14 in-scope "RDA" minutes attachments are re-postings of the
  **combined City Council minutes** the repo already holds; indexed `status=duplicate-not-promoted`.
- **404-purged blobs: 0.** Every listed in-scope minutes attachment was still downloadable.

Two numbers differ and only one is the gap signal:
- **Per-year counts** (below) show repo ≈ PMN each in-scope year — informational only.
- **Per-date set difference** is the real test → 2 recovered council dates.

## How PMN was enumerated (GET-only, polite)

PMN's arbitrary-date search is a CSRF-protected **POST** (`/pmn/searchresult.html`) — disallowed by
the polite-scraper rule. Instead the **GET** cumulative browse endpoint
`/pmn/list/notices.html?id=<bodyId>&page=300` was used; `page` is cumulative (each increment appends
~5 older notices and re-emits the whole list newest-first), so one high page returns the body's
entire history. Saturation:
- Council 653 → **1,020 notices**, 2015 … 2026-07-09 (432 carry a Meeting-Minutes attachment).
- PC 1860 → **612 notices**, 2008-10-08 … 2026-07-08 (43 with minutes).
- RDA 654 → **44 notices**, 2008-10-30 … 2025-06-12 (14 with minutes).

Notice date ≠ meeting date and notice title ≠ doc type, so the meeting date printed **inside** each
downloaded PDF was read before counting (all matched their notice date exactly here).

## City Council (body 653)

| Year | Repo minutes | PMN notices w/ minutes | Per-date gaps repo lacked (recovered) |
|------|-------------:|-----------------------:|:--------------------------------------|
| 2020 | 36 | 35 | 0 |
| 2021 | 32 | 32 | 0 |
| 2022 | 38 | 37 | 0 |
| 2023 | 41 | 38 | 0 |
| 2024 | 35 | 35 | 0 |
| 2025 | 40 | 38 | 0 |
| 2026 | 16 | 17 | 2 (06-04, 06-11 Regular Meetings) |
| **Total (2020+)** | **238** | **232** | **2 recovered** |
| pre-2020 (out of scope) | 0 | 195 | — |

## Planning Commission (body 1860)

| Year | Repo minutes | PMN notices w/ minutes | Per-date gaps repo lacked |
|------|-------------:|-----------------------:|:--------------------------|
| 2020 | 21 | 0  | 0 |
| 2021 | 32 | 33 | 0 |
| 2022 | 26 | 10 | 0 |
| 2023 | 25 | 0  | 0 |
| 2024 | 24 | 0  | 0 |
| 2025 | 23 | 0  | 0 |
| 2026 | 9  | 0  | 0 |
| **Total (2020+)** | **160** | **43** | **0** |
| pre-2020 (out of scope) | 0 | 0 | — |

The CivicClerk PC layer is the superset every in-scope year. PMN attaches PC minutes only in
2021–2022 and the repo already holds all those dates.

## Redevelopment Agency (body 654) — the high-value check, honest zero

CivicClerk has **no RDA category**, so the concern was that standalone RDA minutes might live only
on PMN. **They do not.** PMN body 654 carries 14 in-scope Meeting-Minutes attachments (2020–2024),
all downloaded and read. Each one is the **combined "PARK CITY COUNCIL MEETING MINUTES" document**
for a council meeting date, containing the in-council **Park City Redevelopment Agency Meeting**
recess section — i.e. the exact same document the repo already stores in `meeting_minutes/` from
CivicClerk. Verification per file: (a) internal header reads `CITY COUNCIL MINUTES <date>`;
(b) the notice date exactly matches a date already in `meeting_minutes/minutes_index.csv`;
(c) the repo's council minutes markdown for that date contains the REDEVELOPMENT AGENCY section.

| Year | PMN RDA notices w/ minutes | Exact repo council-date match | Net-new standalone RDA minutes |
|------|---------------------------:|------------------------------:|-------------------------------:|
| 2020 | 6 | 6 | 0 |
| 2021 | 3 | 3 | 0 |
| 2022 | 2 | 2 | 0 |
| 2023 | 1 | 1 | 0 |
| 2024 | 2 | 2 | 0 |
| **Total (2020+)** | **14** | **14** | **0** |

**Conclusion: there is no hidden standalone-RDA minutes layer to promote.** Park City's RDA does not
meet or minute separately from the Council; PMN body 654 is a parallel posting channel for the same
combined council minutes. The repo's existing model (`body=RDA` rows extracted from the in-council
recess inside the council minutes) already captures RDA proceedings. The 14 files are retained here
(`raw/` + `text/`) and indexed `status=duplicate-not-promoted` so a reviewer can confirm equivalence.

## Recovered items (see `index.csv`)

| date | body | title | PMN file | notice | status |
|------|------|-------|---------:|-------:|--------|
| 2026-06-04 | Council | Regular Meeting | 1455537 | 1084097 | recovered (net-new) |
| 2026-06-11 | Council | Regular Meeting | 1455535 | 1085983 | recovered (net-new) |

## What remains genuinely missing / out of scope

- **Nothing in-scope remains unrecovered.** Every PMN Meeting-Minutes attachment dated
  2020-01-01 or later that the repo lacked is now in `index.csv` (the 2 council items).
- **0 source-unavailable (404-purged)** — no listed in-scope attachment had been purged.
- **Pre-2020 PMN minutes** (195 council) are below the 2020 floor and deliberately not downloaded;
  they are enumerated in `raw/_notices_653_p300.html` and `council.json` (file ids present) and
  could be harvested later if the floor is lowered.
- **Housing Authority (657), MBA (655), Historic Preservation Board (659), Board of Adjustment
  (4645)** and other bodies were not cross-checked here (task scoped to Council + PC + RDA). HA and
  MBA proceedings, like RDA, run as in-council recesses already captured in the repo (`body=HA`).
