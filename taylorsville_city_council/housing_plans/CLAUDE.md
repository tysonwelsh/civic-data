# Taylorsville housing_plans — build method & caveats

Additive dataset (Source 2 of `expand-city-sources`): Taylorsville's adopted **General Plan**
(updated 2025, 9 chapters), its **Moderate Income Housing (MIH) element** (General Plan
Chapter 8 + the standalone adopted Ordinance 23-03), and the state DWS/HCD statewide MIH
compilation reports. **Does not modify any existing dataset.** As-of 2026-07-06.

## Contents
```
raw/            14 PDFs verbatim (10 city + 4 state) + _fetch_log.jsonl (polite_fetch provenance)
text/           text sidecars (pdftotext -layout): 10 city full-doc + 4 state per-city page-range extracts
index.csv       provenance table (see columns below)
AVAILABILITY.md what exists, what doesn't, page ranges + contamination checks, audit trail
CLAUDE.md       this file
```

## index.csv columns
`date,title,doc_type,source_url,retrieved_date,format,extraction_method,path,pages,repository,notes`
- **doc_type** ∈ `general_plan` (8 GP chapters) / `mih_element` (2 — GP Ch.8 + Ord 23-03) /
  `mih_annual_report` (3 state compilations) / `compliance_letter` (1 — the SB 34 summary proxy).
- **repository** ∈ `city` (taylorsvilleut.gov) / `state` (jobs.utah.gov HCD).
- **path** is dataset-relative including `raw/` (so `validate_dataset.py` resolves it).
- **format** = `text` everywhere (all sources born-digital; no OCR needed).

## How it was built
1. **Discovery** — the CivicEngage `sitemap.xml` is a sitemap **index**; descended to
   `sitemap-page-1.xml` (160 page URLs) and grepped for general-plan/housing pages →
   `/government/general-plan` and `/government/community-development/moderate-income-housing-plan`.
   The site **403s bare bots** — every fetch used `polite_fetch.py` (browser UA). The General
   Plan chapters are `showdocument/<id>` links wrapped in a docaccess viewer; the MIH page's
   document sits behind a JS docbox widget, so its button target (`Home/ShowDocument?id=3679`)
   was recovered from the static HTML, not the rendered button.
2. **Fetch** — all downloads through `scripts/polite_fetch.py` (`--now 2026-07-06T00:00:00Z`)
   into `raw/`; `raw/_fetch_log.jsonl` records url/status/bytes/sha256/retrieved_utc for all 14.
3. **Extract** — `pdftotext -layout`. City docs → full-document sidecars (one per chapter +
   the standalone MIH ordinance). State compilations → **per-city page-range** sidecars
   `text/taylorsville-<year>.txt` (+ `-sb34`).
4. **Screen** — `screen_corpus.py text/` (clean; only expected footer/hyphen/page-boundary
   flags + the sb34 source garble noted below).
5. **Validate** — `validate_dataset.py taylorsville_city_council/housing_plans` → PASS.

## State-compilation page ranges (the load-bearing extraction detail)
HCD annual reports are **one statewide PDF per year**, cities in **alphabetical blocks**
(Syracuse → **Taylorsville** → Tooele). Ranges bracketed by the next city's header line and
**grep-verified for zero adjacent-city bleed**:

| Report | PDF | Taylorsville pages | Next city (boundary) | Contamination check |
|---|---|---|---|---|
| 2023 | `23reports.pdf` (1109 pp) | **895–911** | Tooele County @912 | 34 TVille / 0 Syracuse / 0 Tooele |
| 2024 | `24reports.pdf` (1030 pp) | **854–861** | Tooele city @862 | 14 / 0 / 0 |
| 2025 | `25reports.pdf` (1303 pp) | **1033–1045** | Tooele city @1046 | 30 / 0 / 0 |
| SB 34 | `sb34.pdf` (199 pp) | **158–166** | TOOELE CITY @167 | 69 / 0 / 0 |

**Block-start marker** (the reliable one, per the South Jordan lesson): the HCD form's first
field — `Type of Jurisdiction` (2023) / `Who is filling out this report?` (2024/2025) / the
`TAYLORSVILLE, CITY` banner (SB 34). Do NOT bracket on an "isolated `X city` header line"
heuristic — this compilation packs columns. **When refreshing, re-derive ranges with the form
marker, then grep each sidecar for `Syracuse`/`Tooele` as the contamination check.**

**SB 34 garble (source, not extraction):** compilation pages **165–166** (Taylorsville's
strategy matrix) render as image/broken-encoding mojibake in the PDF itself; the strategy
narrative on p158–164 extracts clean. `raw/sb34.pdf` retains the pages as-published.

## Dating caveats
- **General Plan → 2025**: no adoption resolution is printed in the chapters; dated by
  Chapter 3's own "the updated 2025 Taylorsville General Plan" wording + Oct/Nov 2025 PDF
  export dates. (Resolution #10-19 in Chapter 1 is a 2010 Wasatch-Choice endorsement — NOT the
  plan-adoption resolution.)
- **MIH element → two dated artifacts.** The current element is General Plan **Chapter 8**
  (2025). The last **formally-adopted** amendment is the standalone **Ordinance 23-03**
  (`ShowDocument?id=3679`), **PASSED Feb 1, 2023** (PC recommended 6-0 Jan 24 2023). Both are
  recorded as `mih_element`; the 2023 ordinance carries the provable adoption date.
- **General Plan chapter ids are not sequential** (Ch.4 Mobility = `showdocument/11619`, before
  Ch.1 = 11621). Harvest by anchor text, not id order.

## Linkage to the rest of the repo
- The MIH element cites the Utah Code 10-9a-403 strategy menu; Taylorsville's adopted
  strategies + their annual implementation status are in the state `mih_annual_report`
  sidecars (`text/taylorsville-2023/2024/2025.txt`) and the SB 34 summary.
- **Ordinance 23-03 joins to `meeting_minutes/all_votes.csv` by date 2023-02-01** (council
  adoption) and to `planning_commission/all_votes.csv` ~2023-01-24 (PC 6-0 recommendation) —
  a concrete cross-body referral for the MIH element.
- Not joined to `db/` — this is a document dataset, not a vote/motion layer.
