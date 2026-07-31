# Orem City campaign-finance disclosures — availability & source hunt

*As-of 2026-07-05.* Additive dataset. This file records every host consulted, what Orem
publishes vs. does not, per-year coverage, and the honest gaps. Utah municipal
campaign-finance filing is fragmented; an honest partial is a valid result.

## Verdict (where Orem filings live)

**Orem publishes candidate campaign-finance disclosures directly on its own election page:
`https://orem.gov/elections/`**, as PDF/image files under
`https://orem.gov/wp-content/uploads/YYYY/MM/`. It is the **authoritative publisher** and
the source for this dataset. The page section is titled *"Municipal financial & Conflict of
Interest disclosures."* Orem does **not** use a third-party filing portal.

**91 campaign-finance filings retrieved, 23 candidates, cycles 2023 & 2025 + annual
reports; ~33 MB.** All fetched GET-only via `harvest.py` (browser UA, ≥1 s throttle,
sha256 + `raw/_fetch_log.jsonl`). Text sidecar for every filing (`text/`, 41 born-digital
`pdftotext`, 50 OCR `tesseract`).

## Hosts tried (in order)

| # | Host / method | Result |
|---|---|---|
| 1 | **`orem.gov/elections/`** (city recorder/elections page) | **HIT — authoritative.** Hosts all live filings (2023 + 2025 cycles + sitting-member annuals) as `/wp-content/uploads/` PDFs. |
| 2 | **EasyVote** (`oremut`/`orem`/`oremcity`.easyvotecampaignfinance.com + `ecf-api.easyvoteapp.com/getwebsiteuser/*`) | **Not a customer.** Subdomains do not resolve (DNS/HTTP 000); the API returns a null-reference error for every Orem sub. Orem is not on EasyVote. |
| 3 | **`disclosures.utah.gov`** (Lt. Governor state disclosures) | **Empty for Orem via GET.** The state keeps Utah-County city folders incl. `Orem City 2019` / `City of Orem 2021` / `Orem 2023` (and an empty `2025` placeholder), but the folder tree loads candidate entities via JS/POST — **all 18 Utah-County city folders render zero candidate entities via GET** (verified across peers; no GET AJAX endpoint, only Qualtrics inline JS; `PublicSearch` is POST-only). Consistent with Utah-County practice: these cities file with the **city**, not the state. Deep enumeration needs POST (outside the GET-only rule); the city site is authoritative regardless. Evidence: `raw/index_pages/disclosures_utah_*`. |
| 4 | **Wayback** (`web.archive.org` CDX for `orem.gov*` / `orem.org*`) | **Partial HIT.** CDX surfaced additional 2023 sitting-member annual disclosures still live (unlinked) on orem.gov (Macdonald, Spencer, Young 2023) — fetched from their live URLs. The **archived 2021 `orem.org/city-elections/` page (2021-10-25)** carries **no filing PDFs** — it points only to a generic `vote.utah.gov` link. No 2019 city-elections capture with filings exists. Evidence: `raw/index_pages/wayback_*`. |
| 5 | **Utah County clerk** (`vote.utahcounty.gov`) | Runs elections & results (already the source for `election_results/`), **not** campaign-finance filings. Not a filing host. |

## Per-year coverage

| Cycle | What Orem publishes | In this dataset |
|---|---|---|
| **2019** | **Nothing online.** Current elections page starts at 2023; no archived 2019 filing PDFs anywhere. | **0 — honest gap.** 2019 winners **Terry Peterson** and **Debby Lauret** have no filing of any kind. |
| **2021** | **No candidate cycle filings online** (archived 2021 page had only a `vote.utah.gov` pointer). | **5 annual reports only** — 2021-elected officials (Young, Millett, Spencer, Macdonald) via their later sitting-member annual statements. No primary/28-day/7-day/final for the 2021 race. |
| **2023** | Full field: Primary / General / Final / Post per candidate + annuals. | **43 filings, 12 candidates** (Muhlestein, McKell, Killpack, Lambson, Rands, Gale, Duerden, A. Williams, Fry, Garber, Carpenter, Sewell) + Lambson/Gale/Killpack/Millett annuals. |
| **2025** | Full field: Primary / 28-day / 7-day / Final (+ Mayor race) + annuals. | **43 filings, 13 candidates** incl. Mayor Young & McCandless. |

## Deliberately EXCLUDED — Conflict-of-Interest (COI) disclosures

The same city page also hosts **personal conflict-of-interest disclosures** (a distinct
genre — *not* campaign contributions/expenditures). Following repo precedent (see Sandy
`campaign_finance/CLAUDE.md`), these are **out of scope** for a campaign-finance dataset
and were **not** ingested. Listed here for recoverability (all `orem.gov/wp-content/uploads/`):

```
2025/06/McCandless-conflict.pdf   2026/02/Gale-COI.pdf        2026/02/Millett-COI.pdf
2025/06/Mecham-conflict.pdf       2026/02/Killpack-COI.pdf    2026/02/Muhlestein-COI.pdf
2025/06/Millett-conflict-1.pdf    2026/02/Lambson-COI.pdf
2025/06/Muehlestein-conflict.pdf  2026/02/McCandless-COI.pdf
```

Non-campaign election documents on the page (canvass stats, certified results, cast-vote
record, precinct map, campaign-manager affidavit) are likewise excluded.

## Election-record cross-check (flag, don't edit)

Every one of the 23 filers **joins `election_results/orem_results_by_candidate.csv`**
(83 filings `exact`, 8 `medium`; **28 of 28 (candidate, year) pairs joined — 100 %**). **No
election-record discrepancy surfaced** — no filer is missing from the election data, and no
filing contradicts it. The only gaps are *coverage* gaps in this dataset (2019 field absent;
2021 candidate filings absent — see table above), not defects in `election_results/`.

## Honesty notes

- **Redaction / completeness is the city's.** Files are served exactly as Orem posted them
  (some are photographed forms, some spreadsheet exports, some signed scans).
- **OCR is machine text** for the 50 scanned/image filings — expect transcription noise;
  the raw PDF/image is authoritative. Screen with
  `.claude/skills/audit-city-data/scripts/screen_corpus.py` (only the scanned files flag,
  as expected).
- **No structured contribution/expenditure tables** were built — filing amounts live only
  in the raw files + `text/` sidecars. A structured `contributions.csv` is a separate,
  out-of-scope layer.
