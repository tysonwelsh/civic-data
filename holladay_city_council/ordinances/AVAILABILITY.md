# Holladay ordinances — availability & gaps

**As-of:** 2026-07-13. Source 3 (adopted zoning/land-use ordinances) of the
`expand-city-sources` skill. **123 ordinances, 2020-01 → 2026-06.**

## What Holladay publishes

| Source | Role | Result |
|---|---|---|
| **American Legal Publishing** (`codelibrary.amlegal.com/codes/holladayut`) | Codified current code host | **Bot-gated (403), current-consolidated text only** — recorded, **NOT mirrored** (per skill rule). Code current through **Ordinance 2026-06, passed 2026-05-21**. |
| **Recorder "Adopted Ordinances" page** (`holladayut.gov/departments/city_recorder/adopted_ordinances.php`) → Revize Document Center | Independent Recorder-certified adopted-ordinance PDFs | **21 PDFs pulled** (`raw/docs/`) — the page is **current-year-only** (2025 + 2026); no back-catalog. |
| **Utah PMN, City Council body 388** | Adopted-ordinance notices | **NOT an adopted-ordinance archive for Holladay.** The cumulative notices list (884 notices, 2008→2026) attaches overwhelmingly **Meeting Minutes** (275) + **Public Information Handouts** (403 = staff reports / *draft* ordinances / budget books). Only **2** notices are ordinance-adoption notices (978897 = a web copy of 2025-02 stormwater; 204019 = 2014-03/04, below floor). Unlike Herriman/Murray, Holladay does **not** post Recorder-certified "Notice of Ordinance Adoption and Summary" PDFs to PMN. |
| **Council/RDA/LBA minutes** (`../meeting_minutes/all_votes.csv`, read-only) | Number → date → subject → motion backbone | **118 ordinance numbers cited in adopting motions** (2020-2026) — the spine of this dataset. |
| **Wayback Machine** (`adopted_ordinances.php`) | Back-catalog recovery attempt | **Only 3 snapshots, all 2025-2026 current-year** — no 2020-2024 listing recovered. |
| **SuiteOne** (`holladayut.suiteonemedia.com`) | Meeting portal | Agenda-packet events only; no separate adopted-ordinance archive (~2025+ depth). Not a distinct ordinance source. |

## Coverage

- **Independent full text (Recorder-certified PDF + text sidecar): 21 ordinances** —
  2025 (02, 03, 04, 05, 06, 08, 09, 10, 11, 14, 15, 16, 20, 21, 22) and 2026 (01-06).
  6 born-digital (`pdftotext`), 15 wet-signature scans (**tesseract OCR @300dpi**).
- **Motion-derived only (`within_source`): 102 ordinances** — witnessed solely by an
  adopting council motion; **high by construction, NOT independently corroborated.**
- Per year: 2020=17, 2021=26, 2022=20, 2023=12, 2024=21, 2025=21, 2026=6.
- **Land-use subset: 39** (rezones, overlays, Title 13 land-use, stormwater, outdoor
  lighting, historic designation, ROW/street vacations, WUI); 84 non-land-use.

## Honest gaps

1. **2020-2024 adopted ordinances have NO independent online full text.** American Legal
   is bot-gated (current text only); the Recorder page is current-year-only; PMN carries
   no certified summaries; Wayback holds no back-catalog. Those **84 rows are
   `within_source`** (`format=na`, `path` blank, `source_url` = the minutes PDF). To read
   what a pre-2025 ordinance actually *did*, request the certified copy from the City
   Recorder or read the consolidated section in the American Legal code.
2. **Recorder page omits some 2025 numbers** (no PDF posted for 2025-01, -07, -12, -13,
   -17, -18, -19). These appear as `within_source` where a motion cites them.
3. **5 independent PDFs have no matching motion (`none`):** 2025-06 and 2026-03/04/05/06
   (2026 items post-date the available minutes; adoption dates taken from each PDF's
   "PASSED AND APPROVED" clause).
4. **2025-02 clerical error preserved:** the posting certificate inside the 2025-02 PDF
   misprints the number as "2025-03"; the ordinance header reads `ORDINANCE NO. 2025-02`
   (stormwater). Held at `medium`. See `linkage_note`.
5. **2025-15** is posted as the clean codified 13.84 text (no ordinance number printed in
   the document); number assigned from the Recorder page label. Held at `medium`.

Nothing here is fabricated: a blank field means "not recorded", and the 84 uncorroborated
back-catalog rows are labeled `within_source`, never `high`.
