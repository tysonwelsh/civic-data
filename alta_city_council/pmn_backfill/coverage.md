# Town of Alta — Utah Public Notice (PMN) minutes cross-check & backfill coverage

**As-of:** 2026-07-13 · **Method:** Source 4 of `expand-city-sources` (GET-only PMN
full-history crawl → per-**meeting-date** set-difference against the audited repo minutes
indexes, ±4-day tolerance). **Result: 5 genuinely-missing minutes documents were
RECOVERED** (3 Town Council, 2 Planning Commission); 0 still-missing after recovery.

Alta's audited `meeting_minutes/`/`planning_commission/` layers were themselves harvested
FROM PMN (bodies 1601/1602), so this pass is primarily a completeness re-audit of that
harvest. Unlike a pure-superset city (e.g. bluffdale), Alta's original harvest **filtered
on PMN's `(Meeting Minutes)` attachment LABEL** and therefore missed minutes that PMN
posted under a different label or filed under the wrong body. Scanning the attachment
**filenames** (not just labels) recovered them.

## PMN entity + body-id discovery (GET-only)

- **Municipality entity:** Town of Alta = **entity id 72**
  (`utah.gov/pmn/list/entities.html?id=3` govType 3 → `.../publicBodies.html?id=72`).
- **All four Alta public bodies** (global ids, not sequential):

  | pmn_body_id | Body | Role | Crawled | All-time notices | Minutes attachments |
  |---|---|---|---|---|---|
  | **1601** | Alta Town Council | council | ✅ | 425 | 149 unique minutes-dates (2015→2026) |
  | **1602** | Alta Planning Commission | PC + Land Use Authority | ✅ | 134 | 32 unique minutes-dates (2015→2025) |
  | **8621** | Budget Committee | fiscal subcommittee | ✅ (inventory) | 9 | 7 minutes-dates (2024→2026) |
  | **1603** | Town of Alta Land Use Appeal Authority | quasi-judicial appeal | ✅ (inventory) | 2 | 1 (a duplicate of a 2023 council meeting) |

- Crawl = the cumulative GET `notices.html?id=<body>&page=300` (entire history in one
  request; the historical *search* is POST/CSRF and was never used — `polite_fetch.py` is
  GET-only). Discovery HTML + notice-list HTML retained under `raw/_disc_*.html` and
  `raw/_notices_<id>_*.html`.

## Coverage — Town Council (repo `meeting_minutes/` vs PMN, 2020 floor)

"PMN mtg-dates" = unique **meeting dates parsed from attachment filenames** carrying a
minutes attachment (any label), bodies 1601 **and** the council meeting mis-filed under
1602. Matched = repo has that date ±4 days.

| Year | Repo docs | PMN mtg-dates | Matched | Recovered | Still-missing |
|---|---|---|---|---|---|
| 2020 | 8 | 10 | 8 | 2 | 0 |
| 2021 | 13 | 10 | 10 | 0 | 0 |
| 2022 | 12 | 9 | 9 | 0 | 0 |
| 2023 | 13 | 13 | 13 | 0 | 0 |
| 2024 | 11 | 11 | 11 | 1 | 0 |
| 2025 | 20 | 20 | 20 | 0 | 0 |
| 2026 | 8 | 7 | 7 | 0 | 0 |
| **Total** | **85** | **80** | **78** | **3** | **0** |

### The 3 recovered council meetings (verified against each PDF's internal header)

| Meeting date | PMN file | Why the original harvest missed it |
|---|---|---|
| **2020-05-06** | 618395 (notice 602689, body 1601) | Attached under the **`Public Information Handout`** label, not `Meeting Minutes` — the label filter skipped it. Internal header: "MINUTES / ALTA TOWN COUNCIL MEETING / Wednesday, May 6, 2020". Fills the May-2020 gap. Born-digital. |
| **2020-06-17** | 618397 (notice 611501, body 1601) | Same `Public Information Handout` mislabel. Header: "ALTA TOWN COUNCIL MEETING / Wednesday, June 17, 2020". Fills the June-2020 gap. Born-digital. |
| **2024-08-14** | 1168819 (notice 935509, **body 1602**) | A **COUNCIL** meeting **mis-FILED under the Planning Commission body** — bundled into the 2024-08-28 PC notice — so the body-1601 council crawl never saw it. Header (OCR): "MINUTES / ALTA TOWN COUNCIL MEETING / Wednesday, August 14, 2024 … Mayor Roger Bourke". Fills the Aug-2024 gap. Image-only scan → OCR. |

## Coverage — Planning Commission (repo `planning_commission/` vs PMN body 1602)

Council-titled and schedule attachments filed under 1602 are excluded from the PC set
(the 2024-08-14 council meeting above is counted under Council, not here).

| Year | Repo docs | PMN PC mtg-dates | Matched | Recovered | Still-missing |
|---|---|---|---|---|---|
| 2020 | 0 | 0 | 0 | 0 | 0 |
| 2021 | 0 | 0 | 0 | 0 | 0 |
| 2022 | 1 | 0* | 0 | 0 | 0 |
| 2023 | 2 | 3 | 2 | 1 | 0 |
| 2024 | 5 | 6 | 5 | 1 | 0 |
| 2025 | 9 | 9 | 9 | 0 | 0 |
| 2026 | 0 | 0 | 0 | 0 | 0 |
| **Total** | **17** | **18** | **16** | **2** | **0** |

\* The 2022-06-02 PC minutes (`22-6-2 …`, 1-digit day) is present in PMN and in the repo;
the auto-parser skips 1-digit-day filenames, so the PMN column is a floor. Every genuine
PC meeting date resolves to a repo doc; **no PC date is a floor artifact**.

### The 2 recovered PC meetings (verified)

| Meeting date | PMN file | Note |
|---|---|---|
| **2023-11-28** | 1089283 (notice 895259) | **DRAFT** minutes (no approved version ever posted to PMN); attached as `Public Information Handout`. Header: "ALTA PLANNING COMMISSION MEETING / Wednesday, November 28th, 2023". Born-digital. Recovered and labeled DRAFT. |
| **2024-04-24** | 1124533 (notice 914855) | Attached as `Public Information Handout` under the 2024-05-22 PC notice. Header: "ALTA PLANNING COMMISSION MEETING / … April 24th, 2024". Born-digital. |

## Sparse-cadence gaps are REAL — PMN cancellation-notice proof

Alta is sparse by design (~12 council mtgs/yr; PC 4th-Wednesday as-needed, "cancelled when
no business"). PMN carries explicit cancellation notices that corroborate the honest gaps:

- **Planning Commission 2020-09-08** — notice 626645 "**Alta Planning Commission –
  Cancelled due to weather**". Direct evidence that the PC's **empty 2020–2021** in the
  repo is an *actively-cancelled / no-business* record, **not** a harvest miss.
- **Planning Commission 2025-06-25** — notice 1005599 "CANCELED – June 25, 2025 Planning
  Commission Meeting" (a specific sparse-month gap, confirmed cancelled).
- **Planning Commission 2026-03-25** — notice 1068103 "CANCELLED – POSSIBLE QUORUM of the
  Alta Planning Commission".
- **Town Council 2025-11-04** — notice 1022301 "Notice of Cancellation of the 2025
  Municipal Election" (+ 990593, the June-2025 election-cancellation notice): the 2025
  municipal election was **cancelled/uncontested**, consistent with the town's tiny
  electorate.

(Pre-floor 2014 council cancellations exist too — out of scope.)

## Inventory only — Budget Committee (body 8621 + council-attached) & Land Use Appeal Authority (1603)

Per task scope these are **inventoried, not built into a core dataset** and are **not**
recovered into `meeting_minutes/`/`planning_commission/`:

- **Budget Committee** — a distinct fiscal subcommittee. Its minutes are split across
  PMN bodies: **1601** (early, filed under the council body: 2021-02-26, 2022-03-01,
  2022-03-18, 2024-03-29, 2024-04-16) and the dedicated body **8621** (2024-04-29,
  2024-11-07, 2025-03-12, 2025-04-24, 2025-05-07, 2026-03-12) — **~11 unique Budget
  Committee meeting dates, 2021→2026**. These are budget/fiscal-subcommittee minutes, not
  Town Council or Planning Commission deliberative minutes, so they are excluded from the
  council/PC diff above. A future task could build a `budget_committee/` dataset if wanted.
- **Land Use Appeal Authority (1603)** — 2 notices; its single minutes attachment
  (fid 1021181, "2023-8-9 TC Meeting Minutes APPROVED") is a **duplicate of the
  2023-08-09 Town Council meeting** the repo already holds (repo fid 1021179). **0 net.**

## Bottom line

- **Recovered minutes: 5** (Council 3 · PC 2). **Genuine still-missing: 0.**
- The recoveries close the repo's **May-2020, June-2020, Aug-2024** council gaps and the
  **2023-11-28, 2024-04-24** PC gaps — all missed by the original harvest's reliance on
  PMN's attachment *label* (they were posted as `Public Information Handout`, and one
  council meeting was mis-filed under the PC body).
- This dataset is **review-only** — do **NOT** merge it into the audited layers without a
  deliberate re-run of the vote extractor / db / weeks pipeline.
