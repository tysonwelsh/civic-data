# housing_plans/ — Midvale availability record

As-of **2026-07-13**. Source 2 of the `expand-city-sources` skill: Midvale City's **General
Plan** + its **Moderate Income Housing (MIH) element** (Utah Code 10-9a-403/408, HB 462 2022),
plus the **state HCD annual reporting** record. Purely additive — no existing Midvale dataset
was touched.

## What EXISTS and was retrieved

### City documents (Revize CMS, `midvale.utah.gov` / `cms1files.revize.com`)
| Doc | date | pages | bytes | format |
|---|---|---|---|---|
| Midvale City General Plan (2016) | 2016 | 112 | 29.9 MB | born-digital text |
| Midvale City Housing Plan (2019) | 2019-11-19 | 52 | 14.1 MB | born-digital text |
| Moderate Income Housing Element for General Plan (2022) | 2022-09-20 | 10 | 175 KB | born-digital text |
| MIH Element (2022 — website variant) | 2022-09-20 | 10 | 285 KB | born-digital text |

- The **MIH Element** was adopted by the **Midvale City RDA Board as an amendment to the General
  Plan on 2022-09-20** (per the city's `housing_plan.php`). It selects **6 of 24** strategies
  from 10-9a-403 with a five-year implementation plan. It exists as a standalone element PDF, NOT
  as a General Plan chapter — the 2016 General Plan predates HB 462.
- Two near-duplicate copies of the 2022 element are published in the RDA Housing Plan folder
  (`Implementation Plan Genera.pdf` = the city-linked copy; `Implementation Plan for We.pdf` =
  a website variant with amended fixed-guideway / strategy-Q wording). Both retained; they are
  the **same adoption**, not two elements.
- The **2019 Housing Plan** is the pre-HB462 moderate-income housing plan / housing element
  (cover: "Adoption Date: 19 Nov 2019"). The RDA folder's `Midvale Housing Plan Adopt.pdf` is
  **byte-identical** (14,076,756 bytes) to the master-plans `Midvale Housing Plan, 2019.pdf` —
  one file, not fetched twice.
- All four city PDFs are **born-digital text** (`pdftotext -layout`, `format=text`). The
  2020–2021 council-minutes OCR seam does NOT apply to this dataset.

### State HCD annual reporting (Utah DWS, `jobs.utah.gov`)
Utah publishes the 10-9a-408 annual implementation reports **only as statewide compilation PDFs**,
not per-city files. **Midvale is PRESENT and reporting in every year checked** (it is well above
the reporting threshold, unlike Alta). The four compilations were **copied sha256-verified from
`bluffdale_city_council/housing_plans/raw/`** (shared statewide files — not re-downloaded); the
`source_url` and `retrieved_date` (2026-07-12) record the true jobs.utah.gov origin. Midvale's
page range within each was located and extracted to a `text/midvale-<year>.txt` sidecar.

| Compilation | total pp | Midvale physical pp | printed / header | next city | sidecar |
|---|---|---|---|---|---|
| `23reports.pdf` (RY 2023) | 1110 | **399–411** | printed 398 (no title pages; printed = physical−1) | Millcreek p412 | `midvale-2023.txt` |
| `24reports.pdf` (RY 2024) | 1031 | **388–398** | "Midvale city" header p388 | Millcreek header p399 | `midvale-2024.txt` |
| `25reports.pdf` (RY 2025) | 1304 | **495–506** | "Midvale city" header p495 | Millcreek header p507 | `midvale-2025.txt` |
| `sb34.pdf` (2019–2021) | 200 | **77–79** | "MIDVALE, CITY" header, summary #40 | Midway p80 (Mapleton p76) | `midvale-sb34-2019-2021.txt` |

**Per-year TOC quirks handled (as flagged in the task):**
- **2023** — the compilation has **no per-city title pages**; the printed footer number = physical−1.
  Ranges were bracketed by each city's *identity block* ("<City>" + "Type of Jurisdiction"):
  Mapleton p390, Midvale p399, Millcreek p412. Because sections don't start on fresh pages, the
  top ~4 lines of p399 are a **Mapleton-tail bleed** (an answer with no city name) — an inherent
  artifact of the no-title-page layout, noted honestly; it carries no other-city identifier.
- **2024** — has "<City> city" header pages, but its **TOC printed numbers can exceed the physical
  count**, so the range was set by **content-scan** of the header pages (Midvale p388 → Millcreek
  p399), not the TOC offset.
- **2025** — offset varies; likewise set by header-page content-scan (Midvale p495 → Millcreek p507).
- All four sidecars were grep-verified for **zero neighbor-city name bleed** (millcreek / mapleton /
  midway / murray / magna = 0 hits each).

**Distinctive Midvale content confirmed** in the state sidecars: Bingham Junction, Jordan Bluffs,
Midvale Main Street TIRA (20% tax-increment set-aside), the 72 East project, the Main Street
Upper-Floor Affordable Housing Initiative, and the Good Landlord program.

## What does NOT exist / was NOT found (honest gaps)
- **No city-published MIH annual report or HCD compliance letter.** The city site's Housing /
  Redevelopment pages publish the General Plan, the 2019 Housing Plan, and the 2022 MIH Element,
  but **no annual 10-9a-408 report copy and no HCD "notice of compliance" letter** (checked
  `redevelopment_agency/housing/*`, `housing_plan.php`, `master_plans_and_studies.php`, the
  community-development landing, and the sitemap on 2026-07-13). Midvale files its annual reports
  **directly with the state** — the state compilation excerpts above ARE the annual-report record.
  This is a publishing pattern, not a data gap. (By contrast Bluffdale posts a city copy + a
  compliance letter; Midvale does not.)
- **No newer General Plan** than 2016 is published — the 2016 General Plan is the current adopted
  land-use plan; the MIH element is the HB462 update layered on top of it by RDA-Board amendment.

## Provenance / method notes
- City PDFs fetched via `scripts/polite_fetch.py` (browser UA, throttled, logged) into `raw/`;
  provenance in `raw/_fetch_log.jsonl`. The four state compilations were **copied** (not fetched)
  and their sha256 re-verified against the bluffdale fetch log (all MATCH); their `_fetch_log.jsonl`
  entries carry a `note` recording the copy + the true jobs.utah.gov origin.
- **Revize URL quirks:** all Document Center paths need `%20`/`%26` encoding; the master-plans
  bare-relative filenames (`2016 Midvale General Plan .pdf`, `Midvale Housing Plan, 2019.pdf`)
  resolve at the **site root** (→ `cms1files.revize.com/midvale/…`), NOT under a Master-Plans
  folder; Revize truncates Document Center filenames to ~25 chars ("Implementation Plan Genera").
- `screen_corpus.py`: 0/8 on all hard flags (no cid/PUA/mojibake/stubs/dupes); the only advisory
  flags are form-template repeated lines, hyphen word-wraps, and page-slice mid-ends — all expected
  for government MIH forms and page-range excerpts. dict_ratio median 0.768.
