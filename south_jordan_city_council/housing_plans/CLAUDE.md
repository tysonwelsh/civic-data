# South Jordan housing_plans — build method & caveats

Additive dataset (Source 2 of `expand-city-sources`): South Jordan's adopted **General Plan**,
its **Moderate Income Housing (MIH) element**, and the state DWS/HCD statewide MIH compilation
reports. **Does not modify any existing dataset.** As-of 2026-07-06.

## Contents
```
raw/            6 PDFs verbatim (2 city + 4 state) + _fetch_log.jsonl (polite_fetch provenance)
text/           text sidecars (pdftotext -layout): 2 city full-doc + 4 state per-city page-range extracts
index.csv       provenance table (see columns below)
AVAILABILITY.md what exists, what doesn't, page ranges, audit trail
CLAUDE.md       this file
```

## index.csv columns
`date,title,doc_type,source_url,retrieved_date,format,extraction_method,path,pages,repository,notes`
- **doc_type** ∈ `general_plan` (1) / `mih_element` (1) / `mih_annual_report` (3 state
  compilations) / `compliance_letter` (1 — the SB 34 summary proxy).
- **repository** ∈ `city` (sjc.utah.gov) / `state` (jobs.utah.gov HCD).
- **path** is dataset-relative including `raw/` (so `validate_dataset.py` resolves it).

## How it was built
1. **Discovery** — crawled `sjc.utah.gov/sitemap.xml`; the General Plan has no standalone
   sitemap page, so descended to `/334/Planning-Zoning` → "General Plan & Supporting Documents"
   section, which carries `DocumentCenter/View/812` (General Plan) and `View/8116` (Appendix A —
   MIH Plan & Housing Study). Do NOT trust stale web-search PDF URLs on this CivicPlus CMS.
2. **Fetch** — all downloads through `scripts/polite_fetch.py` (`--now 2026-07-06T00:00:00Z`)
   into `raw/`; `raw/_fetch_log.jsonl` records url/status/bytes/sha256/retrieved_utc.
   State compilations are the stable generic URLs
   `jobs.utah.gov/housing/affordable/moderate/reporting/documents/{23,24,25}reports.pdf` + `sb34.pdf`.
3. **Extract** — `pdftotext -layout`. City docs → full-document sidecars. State compilations →
   **per-city page-range** sidecars `text/south_jordan-<year>.txt` (+ `-sb34`).
4. **Screen** — `screen_corpus.py text/` (clean; only expected footer/hyphen/page-boundary flags).
5. **Validate** — `validate_dataset.py` → PASS.

## State-compilation page ranges (the load-bearing extraction detail)
HCD annual reports are **one statewide PDF per year**, cities in **alphabetical blocks that
share boundary pages**. South Jordan's blocks (bracketed by the next city, South Ogden, except
2024):

| Report | PDF | South Jordan pages | Next city (boundary) |
|---|---|---|---|
| 2023 | `23reports.pdf` (1109 pp) | **757–770** | South Ogden @ 770 |
| 2024 | `24reports.pdf` (1030 pp) | **692–717** | South Ogden @ 717 |
| 2025 | `25reports.pdf` (1303 pp) | **868–886** | South Ogden @ 886 |
| SB 34 | `sb34.pdf` (199 pp) | **141–142** (entry #69) | South Ogden @ 143 |

**Gotcha (2024):** the 24reports layout does NOT print city names as isolated header lines
(South Ogden/South Salt Lake headers carry trailing text), so an "isolated `X city` line"
heuristic silently over-brackets. The reliable block-start marker is the `Who is filling out
this report?` form field (2024/2025) or the `Type of Jurisdiction` field (2023). A first pass
using the isolated-header heuristic wrongly extended SJ 2024 to p.737 (swallowing South Ogden +
South Salt Lake) and was corrected to p.717. **When refreshing, re-derive ranges with the form
marker, then grep the sidecar for neighboring-city names as a contamination check.**

## Dating caveats
- **General Plan → 2020**: no adoption date/resolution is printed in the document; dated by PDF
  CreationDate (2020-01-31) + "since the 2010 plan" framing. Re-saved 2025-10-13.
- **MIH element → 2025**: Zions Public Finance study dated December 2024, city page labels it
  "2025", PDF created 2025-03-05. It is General Plan **Appendix A**; the two docs are one plan.

## Linkage to the rest of the repo
- The MIH element cites the Utah Code 10-9a-403 strategy menu; South Jordan's adopted strategies
  and their annual implementation status are in the state `mih_annual_report` sidecars
  (`text/south_jordan-2023/2024/2025.txt`). To tie a strategy to a council action, cross-ref
  General Plan / MIH adoption or amendment motions in `meeting_minutes/all_votes.csv` by date.
- Not joined to `db/` — this is a document dataset, not a vote/motion layer.
