# ordinances/ — availability & gap record (Riverton City)

**As-of:** 2026-07-13. **Source type 3** (adopted zoning/land-use ordinances),
`expand-city-sources`. Additive only — nothing in the core layer was modified.

## What was checked

| Source | Result |
|---|---|
| **City codifier** — `codepublishing.com/UT/Riverton` → **eCode360 `RI4763`** | Current-consolidated code text only; **no per-ordinance adopted-PDF archive**. eCode360 dashboard 403s to a bot UA. **NOT mirrored** (bot-gated + consolidated-only). Recorded as the code host in CLAUDE.md. |
| **City Recorder pages** (`/recorder/`, `/recorder/notices.php`) | Revize document-center "Public Notices" list — rolling ~current CC/PC hearing notices (budget, fee schedule, elections), **not an adopted-ordinance archive**. "City Code" link just points back to eCode360. |
| **Utah Public Notice (PMN)** — entity **251** (Riverton) → **City Council body 889** | **THE adopted-ordinance record.** 64 "NOTICE OF ADOPTION — ORDINANCE NO. YY-NN" notices; **62 carry the Recorder-certified signed ordinance PDF** (born-digital). Harvested via the cumulative GET `notices.html?id=889&page=200`. |
| PMN **Miscellaneous** (1099), **Planning Commission** (5473), **RDA** (1101) bodies | No adopted-ordinance PDFs — adoption notices live only on the Council body. |
| **Council minutes** (`../meeting_minutes/all_votes.csv`, 851 motions 2020+) | Motions richly cite `Ordinance No. YY-NN` — **151 distinct numbers** across 2020–2026. The minutes are the backbone for the numbers PMN doesn't carry (2020–2022). |

## What exists (yielded)

- **155 adopted ordinances, adoption window 2020-03-17 → 2026-06-02** (2020 data-floor).
- **62 independent signed-ordinance PDFs** retained in `raw/<num>.pdf` (247 MB, all
  born-digital `text`) with a `text/<num>.txt` sidecar each (**62/62 = 100%** of the PDFs;
  the corpus passed `screen_corpus.py` with no dict/split/weird-char outliers). PMN began
  posting Notice-of-Adoption PDFs in **2023** (4 in 2023, 23 in 2024, 22 in 2025, 13 in
  2026-to-date) — so the 2020–2022 record is minutes-only (`within_source`).
- **Land-use subset: 111** (`land_use=yes`) — Riverton's numbered ordinances are
  overwhelmingly **Title 18 (zoning)** text amendments, rezones, general-plan-map
  amendments, sign/accessory-structure standards, and right-of-way vacations.

## Linkage distribution (see CLAUDE.md for the confidence semantics)

- **high — 58**: number cited in a council motion AND corroborated by an independent PMN
  signed-adoption PDF (`adoption_date` taken from the PDF's "PASSED AND ADOPTED … this Nth
  day of Month YYYY").
- **within_source — 93**: number cited in a council motion but **no independent PMN PDF**
  (mostly 2020–2022, before PMN adoption-PDF posting began; plus 22-11/22-12 CRA plans and
  24-14's amend-repeal cycle). High *by construction*, **NOT** independently corroborated.
- **none — 4**: a PMN signed-adoption PDF exists but **no council motion cites the number**
  (all four rode a consent agenda). Adoption date is source-verified from the PDF;
  `matched_motion_date` is left blank so the row is never read as a corroborated link:
  - **23-14** — Title 2 Ch 55, Office of Police Chief (2023-08-15).
  - **25-09** — Title 2 Ch 105, compensation of elected officials (2025-04-01).
  - **25-19** — electric utility franchise + easement to Rocky Mountain Power (2025-06-03).
  - **26-07** — gas franchise to Questar/Enbridge (2026-04-21; the PMN notice quotes the
    adopting consent-agenda motion, which all_votes captured only as "approve the Consent
    Agenda").

## Gaps / caveats

- **No independent PDFs for 2020–2022 adoptions** — those 93 `within_source` rows rest on
  the minutes alone. Not a scraper miss: PMN's Notice-of-Adoption practice starts 2023.
- **2 PMN adoption notices carry no PDF** (their adoption is stated in the notice body only):
  the combined `NOTICE OF ADOPTION OF ORDINANCES 22-11 AND 22-12` and the `REPEAL ORDINANCE
  NO. 24-14` notice. Both numbers are already covered `within_source` (22-11/22-12) or
  `high` (24-14, whose separate adoption notice 928112 does carry the signed PDF).
- **Consent-agenda adoptions** (the 4 `none` rows) show that some ordinances are adopted
  without a number-bearing roll in the minutes — an extraction/publishing limit, honestly
  flagged, never force-matched.
- **Resolutions are a separate instrument sequence** and are out of scope for this dataset
  (the linkage keys on the word "Ordinance" + number in the motion).
