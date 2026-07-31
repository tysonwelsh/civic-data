# Magna `housing_plans/` — build method & caveats

Source type 2 (moderate-income housing plans + general plan) added by `expand-city-sources`.
**Additive only** — nothing in the existing Magna datasets was touched. As-of 2026-07-13.

## What this dataset is
Magna's adopted **General Plan** (+ appendix), its **Moderate Income Housing (MIH) element**
(current 2022 plan + the adopting ordinance + the prior 2019 plan), and Magna's **annual MIH
implementation reports** as excerpted from the state HCD statewide compilations. Nine rows in
`index.csv` (5 plan documents + 4 state compilation excerpts; §9 `housing_plans` contract
header — validated by `validate_dataset.py`).

## The MSD-staffing fact (why the docs aren't on magna.utah.gov)
Magna is one of the SLCo metro-township-origin entities **staffed by the Greater Salt Lake
Municipal Services District (MSD)**. Its planning documents are hosted on the **MSD CivicPlus
site** (`msd.utah.gov/DocumentCenter/View/<id>`), discoverable from the MSD "Magna General Plan
2021" page (`msd.utah.gov/302`). The city's own `magna.utah.gov` Document Center carries **no**
plan PDFs. Adopting ordinances are on **Utah Public Notice** (`www.utah.gov/pmn/files/<id>.pdf`
— use the `www.` host; `pmn.utah.gov` redirects to HTML). This is the confirmed cluster pattern
(white_city, kearns).

## Document map / lineage
- **General Plan Update, adopted 2021-03-23** (`View/311`, 111 pp) + **Appendix A–H** (`View/312`,
  218 pp). First full General Plan since 2017 incorporation; supersedes the 2009 plan / 2012
  update. Born-digital text.
- **MIH element lineage:**
  - **2019 MIH Plan** (`View/306`, 48 pp) — adopted Nov 2019; **repealed in full** by Ord 22-O-08.
    `format=scanned`: narrative pages are image-based (only data tables carry text, ~16.9k chars).
  - **2022 MIH Plan** (`View/309`, 39 pp) — the **current** element; the exact doc the state 2025
    report cites as Magna's MIH element. Born-digital text.
  - **Ordinance 22-O-08** (PMN `895819`, 81 pp) — the adopting instrument (Magna Metro Township,
    2022-09-27), adopting the 2022 plan as a supplemental General Plan element per Utah Code
    10-9a-403 and repealing the 2019 plan. The PDF bundles ordinance + summary + appended plan.
    Both `View/309` and this ordinance carry `date=2022-09-27` and `doc_type=mih_element`.

## State HCD compilation excerpts (rows 7–10)
The statewide annual-report PDFs (`{23,24,25}reports.pdf` + `sb34.pdf`) are **not per-city files**;
each contains every reporting municipality alphabetically. Per the task's do-not-re-download rule,
the four PDFs are **sha256-verified byte-identical copies** of
`bluffdale_city_council/housing_plans/raw/` (verified after `cp -p`). In `index.csv` the
`source_url` is the true `jobs.utah.gov` URL and `retrieved_date` is Bluffdale's original
(2026-07-12); `raw/_fetch_log.jsonl` carries the original fetch provenance lines (true URL +
sha256 + retrieved_utc), annotated `"note": "sha256-verified copy … NOT re-downloaded"`.

**Magna page ranges** were found by **content-scan** (`magna_locate_pages.py`) — the 2024 TOC page
numbers can exceed the physical layout, so pages were located by scanning each page for
"Magna" / "Magna Metro Township" and bracketing by alphabetical neighbors (Logan before, Mapleton
after). Ranges (physical pages): **2023 = 373–389, 2024 = 367–380, 2025 = 468–484, sb34 = 74–75**.
Boundaries verified clean (no Logan/Mapleton header bleed) before extracting each `text/magna-*.txt`
sidecar. Magna is above the ~5k reporting threshold and is **present in every compilation checked**.

## Extraction & format
- Born-digital PDFs → `pdftotext -layout` sidecars in `text/` (10 sidecars incl. GP appendix).
- The GP prints harmless `Invalid Font Weight` pdftotext warnings (font metadata only) — the text
  layer extracts cleanly (585k chars).
- The **2019 MIH Plan** is the only `format=scanned` row (image narrative pages).
- Corpus screen (`screen_corpus.py text/`): **0** stub/short/dict/split-word/weird-char outliers.
  hyphen-break / repeated-line / ends-mid advisories fire only on long formatted plans and
  page-range extracts — expected.

## Honest gaps (see AVAILABILITY.md)
- **No standalone city-published annual report and no HCD compliance letter** for Magna were found
  (Bluffdale had both; Magna publishes neither). Magna's annual reporting is captured only via the
  state compilation excerpts → **no `compliance_letter` row exists** for Magna. Not fabricated.
- `magna.utah.gov` hosts no plan PDFs; `msd.utah.gov/407` MIH-efforts page is SLCo-unincorporated,
  not Magna.

## Helper script (kept in-dataset)
- `magna_locate_pages.py` — content-scans a state compilation PDF page-by-page for
  Magna/neighbor headers to locate the page range. Uniquely named, lives here (not the shared
  scratchpad) per the standing rule.

## Provenance
`raw/` holds every original verbatim + `_fetch_log.jsonl` (MSD/PMN GETs via `polite_fetch.py`,
frozen `retrieved_utc` 2026-07-13; plus the 4 annotated Bluffdale-copy state-PDF lines). Not yet
loaded into `cities.db` — the orchestrator runs `build_cities_db.py`; this agent does not.
