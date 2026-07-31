# Magna housing_plans — availability & gap record

**As-of:** 2026-07-13. Source type 2 (moderate-income housing plans + general plan) of the
`expand-city-sources` skill. Magna is **MSD-staffed** — its planning documents live on the
**Greater Salt Lake Municipal Services District (MSD) CivicPlus site** (`msd.utah.gov`), not on
`magna.utah.gov`. Adopting ordinances live on **Utah Public Notice (PMN)**. State compilations
come from **Utah DWS Housing & Community Development (HCD)**, `jobs.utah.gov`.

## What exists and was retrieved (9 index rows)

### City / MSD-hosted plans
| Doc | Year | doc_type | Host | pp |
|---|---|---|---|---|
| Magna General Plan Update (complete) | 2021-03-23 | general_plan | MSD DocumentCenter/View/311 | 111 |
| General Plan 2021 — Appendix A–H | 2021 | general_plan | MSD DocumentCenter/View/312 | 218 |
| 2022 Moderate Income Housing Plan (screen version) | 2022-09-27 | mih_element | MSD DocumentCenter/View/309 | 39 |
| Ordinance 22-O-08 adopting the 2022 MIH Plan (+ appended plan) | 2022-09-27 | mih_element | PMN file 895819 | 81 |
| 2019 Moderate Income Housing Plan (prior, superseded) | 2019 | mih_element | MSD DocumentCenter/View/306 | 48 |

- The **General Plan** is hosted on MSD as a single complete adopted PDF (View/311) plus a
  separate appendix (View/312). MSD also splits it into per-element PDFs (Views 572–582); the
  complete adopted document was taken instead to avoid a fragmented, partial capture.
- The **current MIH element** is the **2022 MIH Plan** (View/309) — the exact document the state
  2025 report cites under "Link to general plan, moderate income housing element." Its adopting
  instrument is **Magna Metro Township Ordinance No. 22-O-08** (2022-09-27), the exact URL the
  state report cites under "Link to adoption resolution or ordinance" (PMN 895819). That PMN PDF
  bundles the ordinance + summary + the full appended 2022 plan.
- The **2019 MIH Plan** (adopted Nov 2019, repealed by Ord 22-O-08) is retained for history. Its
  narrative pages are **image-based** (only embedded data tables carry a text layer, ~16.9k
  chars); it is the one `format=scanned` row here.

### State HCD compilations (Magna is ABOVE the ~5k reporting threshold → PRESENT every year checked)
Magna's page range was located by **content-scan** (not the TOC — the 2024 TOC page count can
exceed the physical layout), bracketed by alphabetical neighbors (Logan before, Mapleton after),
checking both **"Magna"** and **"Magna Metro Township"**. No neighbor bleed in any sidecar.

| Compilation | Reports on | Magna present? | Physical pp | Sidecar |
|---|---|---|---|---|
| `23reports.pdf` (2023) | Magna Metro township | YES | 373–389 | text/magna-2023.txt |
| `24reports.pdf` (2024) | Magna city (HB35 seam noted) | YES | 367–380 | text/magna-2024.txt |
| `25reports.pdf` (2025) | Magna city | YES | 468–484 | text/magna-2025.txt |
| `sb34.pdf` (2019–2021 summary) | MAGNA, METRO TOWNSHIP | YES | 74–75 | text/magna-sb34-2019-2021.txt |

The four compilation PDFs are **sha256-verified byte-identical copies** from
`bluffdale_city_council/housing_plans/raw/` (per the task's do-not-re-download rule); their
`index.csv` `source_url` is the true `jobs.utah.gov` URL and `retrieved_date` is the original
Bluffdale retrieval (2026-07-12). Original fetch provenance (true URL + sha256 + retrieved_utc)
is preserved in `raw/_fetch_log.jsonl`, annotated as a verified copy.

## What was checked and NOT found (honest gaps)
- **No 2025/2026 city-published annual MIH report or HCD compliance letter for Magna** was located
  as a standalone file. Bluffdale had a city-hosted copy + a 2025 HCD Notice-of-Compliance letter;
  Magna publishes neither on `magna.utah.gov` nor visibly on the MSD site. Magna's annual reports
  are captured via the **state compilation excerpts** above (2023–2025). No `compliance_letter`
  row exists for Magna — recorded here as an honest gap, not fabricated.
- **`magna.utah.gov` (the city's own CivicPlus site) hosts no planning documents** — its Document
  Center and the MSD "Magna-City" landing page (`msd.utah.gov/351`) link out to the council/PC
  PMN bodies but carry no General Plan / MIH PDFs. All plan documents are on the **MSD**
  DocumentCenter (`msd.utah.gov/302` General Plan 2021, `msd.utah.gov/407` MIH efforts — the
  latter is SLCo-unincorporated, not Magna).
- **No pre-2019 MIH element** exists (Magna incorporated 2017; the 2019 plan is the first).
- **Small area / historic-district plans** (Historic District Mixed-Use zone, ATP) are referenced
  in the annual reports but are out of scope for source type 2 (general plan + MIH only).

## Corpus screen
`screen_corpus.py text/` → 0 stubs, 0 short, 0 duplicate bodies, 0 dict-ratio / split-word /
weird-char outliers across 9 sidecars. The hyphen-break / repeated-line / ends-mid advisories fire
only on the long formatted plans (headers/footers) and page-range extracts — expected, not defects.
