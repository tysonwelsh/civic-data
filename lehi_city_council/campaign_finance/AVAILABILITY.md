# Campaign-finance disclosures — availability & sources checked

**As-of: 2026-07-02.** Dataset for **Lehi City** (Utah County) municipal candidates —
Mayor + City Council — for the **2019, 2021, 2023, 2025** cycles.

**Result: SUBSTANTIALLY COMPLETE (not the usual fragmented/empty Utah-municipal outcome).**
Lehi runs its **own** municipal campaign-finance disclosure and publishes every candidate's
filed report as a PDF on the city website. 134 filings retrieved across the four cycles;
**all 12 general-election winners have at least one filing** (see `index.csv`). 12 specific
2023 report PDFs could not be recovered (documented below + in `unrecovered.csv`).

---

## Where Lehi candidate financial disclosures actually live

**Lehi hosts its own disclosures — it does NOT use the state system for candidate content.**
The Lieutenant Governor's state site (`disclosures.utah.gov`) has a Lehi entry, but it is a
**redirect back to the city page**, not a state-hosted filing (verified — see below). This is
the key finding for Utah cities of Lehi's size: the filings are on the **city recorder's
elections page**, not the county or state.

Two city URLs, reflecting a **CMS migration**:
- **Legacy (WordPress):** `https://www.lehi-ut.gov/government/elections/campaign-finance-disclosures/`
  — a single cumulative page that listed every cycle back to 2009, with PDFs under
  `/wp-content/uploads/<YYYY>/<MM>/<Name>.pdf`. **This page now 404s on the live site** (the
  page and most of its `/wp-content/uploads/` PDFs were dropped in the CMS migration).
- **Current:** `https://www.lehi-ut.gov/government/elections/financial-disclosures/`
  — the new page, covers the **2025** cycle only; PDFs under `/media/<hash>/<name>.pdf`.

Because the legacy page + its 2019/2021/2023 PDFs are gone from the live site, those three
cycles were recovered from the **Internet Archive Wayback Machine** (post-general snapshots of
the legacy page, then the original PDF bytes at their archived capture). The 2025 cycle was
downloaded directly from the live city site.

---

## Sources checked (each URL / query, and what it had)

| Source | URL / query | Result |
|---|---|---|
| **Lehi current disclosures page** | `lehi-ut.gov/government/elections/financial-disclosures/` | ✅ **2025 cycle** — 51 candidate PDFs (13 candidates, mayor + council). Downloaded live. |
| **Lehi legacy disclosures page (live)** | `lehi-ut.gov/government/elections/campaign-finance-disclosures/` | ❌ **404** on live site (page removed in CMS migration). |
| **Lehi legacy page (Wayback)** | `web.archive.org/web/20191118…`, `…20211120…`, `…20231213…/…/campaign-finance-disclosures/` | ✅ Recovered the **2019 / 2021 / 2023** candidate→PDF link lists (cumulative page; also lists 2017/2015/2013/2011/2009, out of scope). |
| **Lehi legacy PDFs (live)** | e.g. `…/wp-content/uploads/2023/12/Nicole-Kunze.pdf` | ❌ **404** on live site — the `/wp-content/uploads/` originals are gone. |
| **Lehi legacy PDFs (Wayback)** | `web.archive.org/web/<ts>id_/…/wp-content/uploads/…pdf` | ✅ 83 of 95 recovered (2019: 27/27, 2021: 20/20, 2023: 36/48). 12 never captured — see below. |
| **State — LG municipal disclosures, Utah county, 2023** | `disclosures.utah.gov/Municipal/utah_2023` | ⚠️ Lists a **"Lehi" entry that redirects to the city page** — NO state-hosted Lehi candidate filings. (State site is used by some other cities, e.g. it links Provo's own recorder page.) |
| **State — LG municipal index** | `disclosures.utah.gov/Municipal/`, `/Municipal/utah` | Organized by county → year folders (2019/2021/2023/2025 exist); **no direct "Lehi" candidate documents** — delegated to the city. |
| **Utah County clerk — financial disclosures** | `utahcounty.gov/Dept/clerk/elections/candidates/FinancialDisclosures.html` | County posts **county/state** candidate disclosures, not Lehi *municipal* candidates (municipal filings are the city's responsibility under Utah Code 10-3-208 / Lehi Code 1-9-4). |
| **Web searches** | "Lehi Utah city council candidate financial disclosure", "…2023 candidates", "lehi-ut.gov media financial disclosure pdf" | Surfaced the city pages above + Lehi Free Press coverage (2019, 2025) that corroborates filers/amounts (not stored — external commentary). |

---

## What was retrieved (see `index.csv`)

| Cycle | Office(s) | Distinct candidates | Filings (PDFs) | Path pattern | Source |
|---|---|---|---|---|---|
| **2019** | Council (3 seats) | 14 | 27 | `/wp-content/uploads/2019-2020/` | Wayback (legacy page) |
| **2021** | Mayor + Council (2 seats) | 12 | 20 | `/wp-content/uploads/2021/` | Wayback (legacy page) |
| **2023** | Council (3 seats) | 15 | 36 | `/wp-content/uploads/2023/` | Wayback (legacy page) |
| **2025** | Mayor + Council (2 seats) | 13 | 51 | `/media/<hash>/` | Live city site |
| **Total** | | | **134** | | |

Each PDF is a **Municipal Campaign Financial Statement** (Utah/Lehi form: combined
contributions "Form A" + expenditures "Form B" + balance). Multiple reports per candidate per
cycle map to the statutory filing points (28 days before primary, before general, post/final).
`filing_type=statement` for all; the specific report period is in `reporting_period`/`title`.
5 filings are marked `amended=yes` (candidate-filed amendments/revisions).

## Gaps — 12 unrecovered 2023 filings (`unrecovered.csv`)

12 report PDFs listed on the 2023 index page were **never captured by Wayback** and **404 on
the live site** (verified via the Wayback availability + CDX APIs and live probes):
- **Michelle Stallings** (winner) — 3 reports missing, but **2 of her reports WERE recovered**.
- **Paige Albrecht** (winner) — 3 missing, **1 recovered**.
- **K. Casey Glade** — 3 missing (incl. one that was a WordPress attachment *page*, not a PDF),
  **1 recovered**.
- **Haley Sousa** — 2 missing, **1 recovered**.
- **Corey Astill** (the 2023-primary withdrawal) — 1 missing, **2 recovered**.

**No candidate is entirely absent** — every 2023 filer (and all 3 winners) has ≥1 recovered
filing. The missing items are specific report instances the Internet Archive did not crawl.

## Notable cross-dataset finding (documented, NOT altering election_results)

The recovered 2019 legacy page has an **"Eliminated at the Primary"** section listing **8
additional 2019 council filers** (Crossette, Montane Hamilton, Tahnee Hamilton, Kneitz, Miles,
Oviatt, Werner, Willis) beyond the 6 general-election candidates. This indicates **Lehi held a
2019 municipal primary** — which the existing `election_results/CLAUDE.md` states did *not*
happen ("6 candidates = 2×seats, so no primary"). These 8 filers are in `index.csv` with
`join_confidence=none` (they are not in `election_results`, which only captured the general).
Flagged here as a data-quality observation for a future `election_results` review; this dataset
is additive and does not modify `election_results`.

## Text-sidecar backfill (2026-07-05)

The dataset originally had **no `text/` sidecars** (a Source-6 conformance gap). Backfilled via
`backfill_text.py`: `pdftotext -layout` for the born-digital PDFs, `pdftoppm 300dpi + tesseract`
for the image-only ones — **134 sidecars written** to `text/`. Measuring the actual text layer
corrected the format labels: **69 born-digital `text` + 65 image-only `scanned`** (the original
index had guessed by file extension and called 64 image-only PDFs born-digital). `build_index.py`
now reads `text_extraction.csv` to set `format`/`extraction_method` per file;
`validate_dataset.py` remains **PASS**. These sidecars feed the additive **structured
campaign-finance layer** (`contributions/expenditures/filing_totals.csv`) — see `CLAUDE.md`.
