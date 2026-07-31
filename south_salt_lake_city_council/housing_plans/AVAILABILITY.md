# housing_plans — availability & verification (South Salt Lake)

**As of:** 2026-07-13. Built by the `expand-city-sources` skill (Source 2, moderate-income
housing). Additive dataset — nothing in any existing South Salt Lake dataset was modified.

## What was checked

Two source families, per the skill:

1. **City** (`sslc.gov`, CivicPlus / CivicEngage Central). Discovered by crawling
   `https://sslc.gov/sitemap.xml` (NOT stale search-result URLs), then navigating the
   **Moderate Income Housing** page (`/522/Moderate-Income-Housing`), the **Housing &
   Resources** page (`/519/Housing-Resources`), the **Community Development**
   (`/213/Community-Development`) and **Planning & Zoning** (`/216/Planning-Zoning`) pages.
   Docs are CivicEngage `/DocumentCenter/View/<id>` links. **The `/522` MIH page is a pure
   narrative page with no document links** — SSL's MIH element lives inside the General Plan
   plus two standalone MIH Plan PDFs (2016, 2023), all linked from `/519/Housing-Resources`.
   Cross-read the state annual-report "Link to Plan/Ordinance" fields, which surfaced the
   General Plan 2040 Appendix (`View/312`) and confirmed the `View/247` GP link.
2. **State HCD** — Utah Dept. of Workforce Services, Housing & Community Development, index
   `https://jobs.utah.gov/housing/affordable/moderate/reporting/`. The annual reports are
   **statewide compilation PDFs, not per-city files** (`{23,24,25}reports.pdf`), plus the
   `sb34.pdf` SB 34 Municipal Progress Summaries (2019–2021). These four compilations were
   **NOT re-downloaded** — copied sha256-verified from `bluffdale_city_council/housing_plans/raw/`
   (identical bytes; the true `jobs.utah.gov` `source_url` and original retrieved_date
   2026-07-12 are recorded in `index.csv`). See the Provenance note below.

## What was FILED / retrieved (8 index rows, 8 raw PDFs, 8 text sidecars)

### City documents (4 PDFs, all born-digital text)
- **General Plan 2040** ("Our Next Move") — General Plan Update **adopted Aug 17 2021**
  (`View/247`, 111 pp). Current land-use context and the **container of the MIH element**: the
  Implementation Strategy chapter carries the moderate-income-housing goal ("Update the City's
  Moderate Income Housing plan … annually") and cites Utah Code 10-9a-403.
- **General Plan 2040 Appendix** — Market Analysis Report + technical appendices
  (**Aug 11 2021**, `View/312`, 103 pp).
- **Moderate Income Housing Plan 2016** — the **standalone MIH element, adopted by the City
  Council on 2016-08-11** (`View/456`, 38 pp; Deborah A. Snow, Chair; Cherie Wood, Mayor). The
  pre-HB462 element.
- **Moderate Income Housing Plan & Needs Assessment (2023)** — the **updated MIH Plan**
  (`View/1996`, 61 pp; prepared by James Wood, Sept 2023). The city page labels it "2023 SSL
  Housing Needs Assessment", but the document's own title is *"Moderate Income Housing Plan and
  Needs Assessment for South Salt Lake"* — i.e. it is the "enhanced/updated MIHP" the state
  annual reports say SSL commissioned. Analytical plan; no formal council-adoption date printed
  inside it (classified `mih_element`).

### State HCD compilations (4 PDFs — South Salt Lake present in ALL of them)
Each statewide compilation's SSL page range was located (bracketed by the alphabetical
neighbors **South Ogden** above and **South Weber** below) and extracted to a `text/` sidecar,
then **grep-verified for zero neighbor-city bleed**:

| Compilation | Total pp | SSL (physical) pp | Bracketed by | Sidecar |
|---|---|---|---|---|
| `23reports.pdf` (RY 2023) | 1109 | 782–792 (printed 781–791) | South Ogden p770 / South Weber p793 | `text/south_salt_lake-2023.txt` |
| `24reports.pdf` (RY 2024) | 1030 | 729–736 | South Ogden p717 / South Weber p737 | `text/south_salt_lake-2024.txt` |
| `25reports.pdf` (RY 2025) | 1303 | 897–908 | South Jordan p868 / South Weber p909 | `text/south_salt_lake-2025.txt` |
| `sb34.pdf` (SB 34 2019–2021) | 199 | 144–145 | South Ogden p143 / South Weber p146 | `text/south_salt_lake-sb34-2019-2021.txt` |

**South Salt Lake is present in every state filing year checked** (RY 2023/2024/2025 annual
reports + the 2019–2021 SB 34 progress summary) — expected, as SSL (~26k pop.) is well above
the state reporting threshold. SB 34 header: County Salt Lake, AOG/MPO WFRC, 4 required items,
major transit investment corridor YES. The absence of a *standalone per-city report file* on
the state site is **expected** (the state publishes only statewide compilations), NOT a gap.

## Per-year page-range quirks (bracketing, not TOC)

Per the skill's per-year notes, page ranges were fixed by **content scan / alphabetical
bracketing**, not by trusting each compilation's TOC:
- **2023** — no title pages, so printed = physical − 1. SSL section title line "South Salt
  Lake" sits on **physical p782** (printed 781); confirmed by the standalone city-title-line
  pattern (South Ogden p770 → SSL p782 → South Weber p793, ~11 pp apart).
- **2024** — clean per-section headers ("South Salt Lake city" p729); South Weber header at
  p737 bounds the section at pp 729–736.
- **2025** — header "South Salt Lake city" at physical p897; South Weber at p909 → pp 897–908.
  (A stray "South Salt Lake" mention at p512 is a cross-reference inside another jurisdiction's
  narrative, not the SSL section — verified.)

## What is NOT filed / not applicable

- **No HCD "Notice of Compliance" / compliance-letter PDF on the city site.** Unlike Bluffdale,
  SSL does not post the annual HCD compliance letter to its own DocumentCenter. This is **not a
  gap**: SSL's compliance is evidenced by its presence in the statewide annual compilations
  (RY 2023/2024/2025). `doc_type=compliance_letter` therefore has **zero rows** — an honest
  absence, not a missing fetch.
- **No standalone per-city report PDF on the state HCD site** — expected; the state publishes
  only the statewide compilations.
- **No pre-2023 annual-report compilation** is linked on the current HCD index (earliest is
  `23reports.pdf`); the 2019–2021 window is covered by the SB 34 summary. No honest gap: HB 462
  annual reporting under the current form begins with RY 2023.

## Extraction & verification method

- All 8 raw PDFs are **born-digital** (text layer present; `pdftotext -layout` yields clean
  text — the SSL council-minutes coverage cliff / OCR concerns do NOT apply here).
  `extraction_method = pdftotext -layout`, `format = text` for every row.
- Every city raw byte fetched through `scripts/polite_fetch.py` (browser UA, throttled, logged);
  provenance in `raw/_fetch_log.jsonl` (all HTTP 200, `application/pdf`). The 4 state-file
  provenance lines were carried over verbatim from the sha256-identical bluffdale fetch.
- Corpus screened with `audit-city-data/scripts/screen_corpus.py`: **0 cid_artifacts,
  0 replacement_chars, 0 PUA_garbled, 0 mojibake, 0 long_tokens, 0 stubs, 0 duplicate_bodies,
  0 read_errors, 0 dict_ratio outliers, 0 split_word outliers** across all 8 sidecars.
  Advisory `hyphen_breaks` / `repeated_line` / `ends_mid` flags are expected artifacts of the
  designed planning-document layout (repeated running headers, column hyphenation), not
  extraction defects.
- **One weird-char advisory** — `text/general-plan-2040-appendix.txt` (weird-char ratio 3.3%).
  Investigated: the appendix uses heavy custom-design fonts (`pdftotext` emitted "Invalid Font
  Weight" warnings), whose decorative bullet/icon glyphs land in the C1 control range
  (`\x87`, `\x96`, `\x90`, …). The **narrative text and all data tables extract fully and
  cleanly** (e.g. the "Potential Supportable Retail Square Footage" NAICS table). This is a
  designed-layout glyph artifact, not garbled OCR or hallucinated text — retained verbatim.

## Provenance note (do not "fix")

The four `hcd-*.pdf` state compilations are **byte-identical copies** (sha256-verified) of the
files already retrieved for Bluffdale on 2026-07-12 — one download of a statewide compilation
serves every city in it. `index.csv` records the **true `jobs.utah.gov` `source_url` and the
original 2026-07-12 `retrieved_date`**, not the copy date. This is the sanctioned
"copy-don't-re-download" path for the shared statewide compilations; the SSL-specific work is
the page-range location + bleed-verified sidecar extraction.
