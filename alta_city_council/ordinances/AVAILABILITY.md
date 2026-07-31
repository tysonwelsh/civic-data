# Town of Alta — `ordinances/` availability & gap record

**As-of:** 2026-07-13. **Scope:** adopted Town Council **ordinances** (the `YYYY-O-N`
series), 2020 → present. Resolutions (`YYYY-R-N`) are OUT of scope for this dataset.

## What exists / was retrieved

- **Primary source — the town's own adopted-ordinance list:**
  `https://townofalta.utah.gov/ordinances-resolutions/` is a **static HTML page** (not the
  JS `/meetings/` app) that lists every ordinance and resolution by number with a direct
  Google Cloud Storage PDF link (`storage.googleapis.com/juniper-media-library/130/…`). The
  page itself is retained at `raw/_ordinance_list_page.html` as the enumeration provenance.
- **44 ordinance PDFs retained** in `raw/` (one per adopted, posted ordinance),
  `2021-O-1` → `2026-O-12`, ~12 MB. Every PDF has a `text/<no>.txt` sidecar:
  - **19 born-digital** → `pdftotext -layout` (`format=text`).
  - **25 scanned/signed** → `tesseract 5 OCR @300dpi` via `pdftoppm` (`format=scanned`).
    (Most 2024→2026 ordinances are scanned signature-page PDFs.)
- **6 no-PDF rows** (`format=na`) for ordinance numbers the town **adopted or acted on but
  never posted a standalone PDF for** — witnessed only by the council minutes
  (`match_confidence=within_source`; `source_url` points at the witnessing PMN minutes
  file, `matched_motion_date`/`_no` into `meeting_minutes/all_votes.csv`):
  `2020-O-4`, `2020-O-5` (not on the town list at all — minutes-only), `2021-O-6`,
  `2022-O-3`, `2023-O-5` (town list marks these "Did Not Pass"), `2026-O-3`
  (town list: "continued to June" — superseded by the June `2026-O-11` Zoning Map).

**Total index rows: 50** (44 with retained PDF + 6 within_source). Adoption dates span
**2020-10-14 → 2026-06-26**. Land-use / zoning subset: **10** ordinances.

## Gaps and honest limits

- **2020 ordinances `2020-O-1..O-3` were not located** anywhere (not on the town list, not
  cited in the 2020 minutes we hold). The town's online ordinance list starts its
  **ordinance** section at 2021 (only *resolutions* go back to 2018 on that page). Alta is a
  ~380-person town; a sparse/renumbered early-2020 ordinance record is expected, not a
  scraper miss.
- **`2021-O-2` dropped as a zero-information ghost.** The town list shows it "Did Not Pass"
  with **no subject and no PDF**, and no council vote motion cites it. Rather than fabricate a
  dated row, it is recorded here as a known numbering gap only.
- **Linkage limit — 2024–2025 minutes cite ordinances inconsistently.** Alta's vote motions
  cite the ordinance number in most years (often as the digit form `2024-0-4`, not the
  letter `2024-O-4` — both are handled), but **4 posted ordinances are not cited by number in
  any council vote motion** and stay `match_confidence=none`: `2022-O-6`, `2024-O-7`,
  `2024-O-8`, `2026-O-12` (2026-O-12 is July 2026, after the newest minutes we hold,
  2026-06-17). Their PDFs are retained and independently sourced; only the motion cross-link
  is absent.

## Sources checked

1. **Town adopted-ordinance list** (`/ordinances-resolutions/`) — the authoritative online
   archive; used for enumeration + PDF retrieval. ✅ primary.
2. **`meeting_minutes/all_votes.csv`** — the motion backbone; used for the number→date→motion
   cross-link (`high`) and to witness the no-PDF ordinances (`within_source`).
3. **Utah PMN council body 1601** (`/pmn/list/notices.html?id=1601`) — scanned; Alta bundles
   every attachment under the generic label **"Public Information Handout"** and posts **no
   separately-labeled "Notice of Ordinance Adoption"** PDFs (unlike Murray/Draper/Riverton).
   So PMN was NOT a distinct ordinance source here; the town's own list is richer.
4. **Codified municipal code — American Legal Publishing** (see `CLAUDE.md`). Consolidated
   current text only, **bot-gated (403)** — recorded, **not mirrored**.
