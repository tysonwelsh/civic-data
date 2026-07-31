# Bluffdale — Utah Public Notice (PMN) minutes cross-check & backfill coverage

**As-of:** 2026-07-12 · **Method:** Source 4 of `expand-city-sources` (GET-only PMN
crawl → per-date set-difference against the repo minutes indexes). **Result: the repo is
a complete SUPERSET of every genuine minutes document PMN holds for Bluffdale — 0 minutes
recovered, 0 genuine gaps.** This is the expected, honest outcome (recon: the CivicPlus
city portal covers the 2020 floor fully; PMN is a thin cross-check mirror).

## PMN body-id discovery (GET-only)

- **Municipality entity:** Bluffdale = **entity id 87**
  (`utah.gov/pmn/list/entities.html?id=3` → `.../publicBodies.html?id=87`).
- **Bluffdale public bodies** (all 16 listed; the council-/PC-minutes-bearing ones crawled):

  | pmn_body_id | Body | Crawled | Family | Notices | Minutes attachments (all-time) |
  |---|---|---|---|---|---|
  | **373** | City Council | ✅ | council | 1032 | 209 |
  | **4905** | City Council & Local Building Authority | ✅ | council | 98 | 54 |
  | **2803** | City Council & Planning Commission | ✅ | council | 198 | 36 |
  | **2781** | City Council and Redevelopment Agency Board | ✅ | council | 10 | 2 |
  | **374** | Planning Commission | ✅ | pc | 665 | 137 |
  | 8955 | (Inactive) Planning Commission & Board of Adjustments | ✅ | pc | 0 | 0 |
  | 375 | Board of Adjustments | — | (quasi-judicial) | — | — |
  | 376 / 2146 / 2574 / 7045 / 8391 / 8397 / 8399 / 8533 / 8535 | Arts Council, Tree Board, RDA Taxing Entity Cmte, Historic Preservation, Healthy Bluffdale, Community Garden, Youth Council, Budget Review, Audit Cmte | — | non-council/PC boards (out of scope) | — | — |

  Bluffdale's council convenes its **RDA / LBA / joint-PC** sessions *in-session inside the
  same combined minutes PDF*; PMN posts that one combined document redundantly under
  several council-family body ids (373, 4905, 2803, 2781). They are therefore unioned into
  one **council family** for the by-date cross-check (the repo `meeting_minutes/` dataset
  already carries RDA/LBA as `body` tags within the same docs).

## Coverage — Council family (repo `meeting_minutes/` vs PMN, 2020 floor)

Crawl was the cumulative GET `notices.html?id=<body>&page=300` (entire history in one
request). "PMN minutes-dates" = unique meeting dates carrying a `(Meeting Minutes)`
attachment across bodies 373+4905+2803+2781. Matched = repo has that date ±4 days.

| Year | Repo minutes docs | PMN minutes-dates | Matched in repo | Still missing |
|---|---|---|---|---|
| 2020 | 23 | 21 | 21 | — |
| 2021 | 24 | 21 | 21 | — |
| 2022 | 21 | 20 | 20 | — |
| 2023 | 22 | 11 | 10 | (1 mislabel, see below) |
| 2024 | 18 | 3 | 3 | — |
| 2025 | 23 | 0 | 0 | — |
| 2026 | 14 | 0 | 0 | — |
| **Total** | **145** | **76** | **75** | **0 genuine** |

PMN stops attaching *minutes* after early 2024 (it keeps posting agendas); the city
CivicPlus portal carries all 2024–2026 minutes, so those years are 100% repo-covered with
no PMN minutes to compare.

### The single non-match — 2023-11-14 (verified, NOT a gap)

PMN notice **872517** (body 373) attaches file **1047617** labeled `(Meeting Minutes)`,
but the file is `20231114 NOTICE OF QUORUM 14400.pdf`. Fetched and verified against its
own header + internal date:

> "BLUFFDALE CITY COUNCIL — NOTICE OF QUORUM … a quorum of the Bluffdale City Council may
> be attending the **Open House for the 14400 South Construction** … Tuesday, November 14,
> 2023 … **NO OFFICIAL CITY BUSINESS WILL BE CONDUCTED** … no vote or action will be taken."

This is a §52-4-203(7) open-house quorum notice, **not deliberative meeting minutes** —
PMN mislabeled the attachment type (the documented "VERIFY before trusting PMN's own label"
caveat). It is retained in `raw/` and catalogued in `index.csv` for provenance, but it is
**not** a recovered minutes document and does not represent a gap in the audited layer.

## Coverage — Planning Commission (repo `planning_commission/` vs PMN body 374)

| Year | Repo minutes docs | PMN minutes-dates | Matched in repo | Still missing |
|---|---|---|---|---|
| 2020 | 14 | 13 | 13 | — |
| 2021 | 17 | 16 | 16 | — |
| 2022 | 12 | 11 | 11 | — |
| 2023 | 13 | 13 | 13 | — |
| 2024 | 13 | 1 | 1 | — |
| 2025 | 14 | 0 | 0 | — |
| 2026 | 8 | 0 | 0 | — |
| **Total** | **91** | **54** | **54** | **0** |

Every PMN PC minutes date is present in the repo. Body 8955 (inactive PC & Board of
Adjustments) holds 0 notices.

## Bottom line

- **Recovered minutes: 0.** **Genuine gaps: 0.** The repo `meeting_minutes/` (145 docs)
  and `planning_commission/` (91 docs) fully cover — and exceed — PMN's Bluffdale minutes
  holdings (76 council-family + 54 PC minutes-dates, all matched).
- The lone catalogued row is the 2023-11-14 mislabeled quorum notice, kept for honesty and
  provenance, not as recovered minutes.
- Do **not** merge this dataset into `meeting_minutes/` or `planning_commission/`.
