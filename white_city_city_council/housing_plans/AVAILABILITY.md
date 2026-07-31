# housing_plans — availability & verification (White City)

**As of:** 2026-07-13. Built by the `expand-city-sources` skill (Source 2, moderate-income
housing). Additive dataset — nothing in any existing White City dataset was modified.

**Headline finding: NOT an honest-empty.** Despite White City's small size (~5,000 pop.) and
its 2017–2024 metro-township / MSD-staffed status, it **files a moderate-income housing report
under its OWN name every year checked** and has a **standalone adopted MIH Plan** — it is NOT
below the reporting threshold and is NOT absorbed under the Greater Salt Lake MSD in the state
record. 8 indexed docs (5 raw PDFs fetched here + the 3 shared state compilations + SB34).

## What was checked

Two source families, per the skill:

1. **City / MSD.** White City runs on a tiny **Streamline** CMS (`whitecity.utah.gov`, PDFs on a
   Cloudfront CDN at `/files/<hash>/`; legacy mirror `whitecity.specialdistrict.org`). Its
   long-range planning (incl. the MIH element) is **staffed by the Greater Salt Lake Municipal
   Services District (GSL-MSD)**, so the adopted MIH Plan + its ordinance live on **`msd.utah.gov`**
   (`/446/Moderate-Income-Housing-Plan` → CivicPlus `/DocumentCenter/View/…`) and the GSL-MSD
   **ArcGIS Hub** (`wc-lrp-gslmsd.hub.arcgis.com`), not the city Streamline site. Checked: the
   Planning Commission page (`/planning-commission` — exposes only a meeting-schedule PDF + the
   General Plan), the `/meetings-archive` page (holds the 2019 MIH hearing notice + element
   timeline + GP drafts), and the MSD White City / MIH pages.
2. **State HCD** — Utah Dept. of Workforce Services, Housing & Community Development, index
   `https://jobs.utah.gov/housing/affordable/moderate/reporting/`. Annual reports are **statewide
   compilation PDFs, not per-city files** (`{23,24,25}reports.pdf`) plus the `sb34.pdf` SB 34
   Municipal Progress Summaries (2019–2021).

## What was FILED / retrieved (8 index rows)

### City / MSD documents (4 PDFs fetched here)
- **General Plan (adopted April 2022)** — `whitecity.specialdistrict.org/files/ea3ef2b51/…`, 190 pp,
  53 MB, born-digital. **Embeds the Moderate-Income Housing element as Appendix C**; the narrative
  records the **original Housing Element adopted 2019-11-14** after a Sept 2019 open house
  (SB 34 menu-item voting — White City residents voted for 14 of 23 items).
- **White City Moderate Income Housing Plan (2022 FINAL)** — the **standalone** MIH element
  (`msd.utah.gov/DocumentCenter/View/673`, 50 pp, born-digital), "a supplemental element of the
  2022 White City General Plan." GSL-MSD-staffed (PC Vice-Chair Christy Seiger-Webster).
- **MIH Adopting Ordinance 22-09-01** — the adopting-ordinance package (`View/1200`, 57 pp,
  born-digital), 2022-09-01, includes the plan text.
- **MIH public-hearing notice (2019-11-14, signed)** — the adoption record of the FIRST (2019)
  Housing Element (`whitecity.utah.gov/files/7b0c949ec/…`, 1 pp, **scanned** → tesseract OCR).

### State HCD compilations (4 — White City PRESENT in ALL of them)
Each statewide compilation was **sha256-verified-copied from `bluffdale_city_council/housing_plans/raw/`**
(they are shared statewide PDFs; do NOT re-download — see CLAUDE.md). White City's alphabetical
page range was located (bracketed by the next city, **Woods Cross**) and extracted to a `text/`
sidecar, then grep-verified for zero neighbor-city bleed:

| Compilation | Total pp | White City (physical, 1-based) pp | Sidecar | Filer |
|---|---|---|---|---|
| `23reports.pdf` (RY 2023) | 1109 | **1090–1097** | `text/white_city-2023.txt` | GSL-MSD (Woods Cross starts p1098) |
| `24reports.pdf` (RY 2024) | 1030 | **1016–1022** | `text/white_city-2024.txt` | Morgan Julian, MSD (Woods Cross starts p1023) |
| `25reports.pdf` (RY 2025) | 1303 | **1280–1293** | `text/white_city-2025.txt` | Daniele Benigni, MSD (Woods Cross starts p1294) |
| `sb34.pdf` (SB 34 2019–2021) | 199 | **197** (single landscape page) | `text/white_city-sb34-2019-2021.txt` | entity #96 "WHITE CITY, METRO TOWNSHIP" |

**Per-year presence / absence (the honest check the task asked for):**

| State filing year | Present? | Reported as | Notes |
|---|---|---|---|
| SB 34 2019–2021 | **PRESENT** | WHITE CITY, METRO TOWNSHIP (#96) | 3 required + 3 total menu items; County Salt Lake; WFRC. Cites "White City Metro Township MIH Plan 2019". |
| RY 2023 | **PRESENT** | White City | ADU / IADU strategy; internal ADUs approved June 2023 in 100% of SF zones. |
| RY 2024 | **PRESENT** | White City | filed by MSD Long-range Planner; ADU + Walk White City transportation plan. |
| RY 2025 | **PRESENT** | White City | filed by MSD Long Range Planner; cites "White City Moderate Income Housing Plan 2020". |

There is **no RY 2022 statewide compilation** on the current HCD index (earliest is `23reports.pdf`);
the SB 34 summary covers 2019–2021, so there is no honest gap between the SB34 window and RY 2023.

## Threshold / MSD-reporting status (the task's core question)

- **NOT below the reporting threshold.** White City files a full 10-9a-408 moderate-income housing
  report under its own name in every year the state has published (SB34 2019–2021, RY 2023/2024/2025).
  Utah's MIH annual-reporting duty applies to municipalities that have adopted a plan; White City
  adopted one (2019, updated 2020, finalized 2022) and reports against it. (This is unlike Alta,
  which is genuinely tiny/sparse — White City at ~5k is above the practical floor and actively files.)
- **Reported under its OWN identity, staffed by GSL-MSD — NOT absorbed under the MSD.** The reports
  are authored/submitted by **Greater Salt Lake MSD Long-Range Planning staff** on White City's
  behalf (Morgan Julian 2024, Daniele Benigni 2025), and the plan/ordinance are hosted on
  `msd.utah.gov`, but the **entity of record in the state compilation is "White City" (metro
  township pre-2024, city after)** — there is no separate "Greater Salt Lake MSD" umbrella entry
  standing in for it. The township→city transition (HB 35, 2024-05-01) does not create a reporting
  gap: SB34 files it as "White City, Metro Township"; RY 2023–2025 file it as "White City".

## What is NOT filed / not applicable

- **No standalone per-city report PDF on the state HCD site** — expected; the state publishes only
  the statewide compilations. Not a gap.
- **No HCD compliance / notice-of-compliance LETTER found** for White City (Bluffdale has one on
  its city site; White City's Streamline/MSD sites post none). The statewide compilation is the
  report of record. Recorded as an honest absence — no `compliance_letter` row.
- **Retained but not indexed** (out of the `doc_type` vocab — administrative process artifacts,
  kept in `raw/` for provenance): `moderate-housing-element-timeline.pdf` (a 2-page 2019 GSL-MSD
  MIH-element adoption-schedule worksheet for White City + Magna). The GP *drafts*
  (`…draft_general_plan.pdf`, `10.21.2021…general_plan_draft.pdf`) and the standalone GP transportation
  element on `/meetings-archive` were **not** captured — the ADOPTED April-2022 General Plan supersedes
  them.

## Extraction & verification method

- The 4 city/MSD PDFs are **born-digital** except the 1-page 2019 hearing notice (scanned →
  tesseract 5.5 OCR at 300 dpi; `format=scanned`). `pdftotext -layout` yields clean text for the rest.
- The 4 state compilations are the **shared statewide HCD PDFs**, sha256-verified-copied from the
  bluffdale build (identical bytes — see `raw/_fetch_log.jsonl` and CLAUDE.md); White City excerpts
  extracted by physical page range (pymupdf) bracketed by the next city (**Woods Cross**), each
  sidecar grep-verified to contain "White City" and **zero** Woods Cross / West Valley / neighbor
  strings. First page of the 2023/2024 excerpts carries a fragment of the previous city's last
  form-field (a split page) — no neighbor city name, no substantive bleed.
- Every fetched raw byte went through `scripts/polite_fetch.py` (browser UA, throttled, logged);
  provenance in `raw/_fetch_log.jsonl` (city fetches HTTP 200 `application/pdf`; the 4 HCD rows are
  copy-provenance records carrying the true `jobs.utah.gov` URL + original retrieval timestamp).
- Corpus screened with `audit-city-data/scripts/screen_corpus.py` over the 8 sidecars: **0 mojibake,
  0 long-token, 0 stub, 0 duplicate-body, 0 dict-ratio, 0 weird-char, 0 read errors.** The single
  `split_word` outlier is the OCR'd 2019 notice (expected for scanned text; its 0.90 dict-ratio is
  clean); the `ends_mid` advisories are the expected artifact of extracting page-range excerpts from
  the HCD web-form report layout; the one `hyphen_breaks` flag is the multi-column magazine layout of
  the 190-page General Plan.
