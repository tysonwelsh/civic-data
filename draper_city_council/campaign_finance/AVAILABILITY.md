# campaign_finance/ — availability & gap log

As-of **2026-07-13**. Additive acquisition-only dataset; no existing dataset modified.
In-scope cycles: **2021, 2023, 2025**. Older cycles (2011–2019) were acquired too because
the city's records portal made them trivially available (see "Sources" below) — an
unplanned bonus that extends the money→votes chain back to 2011.

## Sources (three, complementary — the 2023 story is the headline)

1. **City website CF page (live)** —
   `https://www.draperutah.gov/city-government/elections/campaign-finance-disclosures/`
   holds the **2025 cycle only** (23 filing PDFs under `/media/<hash>/…`). The elections
   pages are rewritten each cycle ("information will be posted on this page" between
   cycles), so this page's content will turn over in 2027 — harvest before then.
2. **Tyler Content Manager "Search All Online Records" GRAMA portal** —
   `https://drapercityut.contentmanager.tylerapp.com/tylercm/web/` (Tyler EagleWeb; guest
   entry via a disclaimer acknowledgment; GET-navigable). Its **"Elections" document
   class holds per-candidate campaign records for 2011–2025** — 100 catalog nodes, 255
   attachments, including **every 2021 filing and the ONLY surviving copies of the 2023
   filings**. This portal is the authoritative city archive; the Tyler PDFs are
   byte-identical (sha256) to the city-page PDFs where both exist.
3. **Wayback Machine** — the 2021 cycle was also published on the old CivicPlus site
   (`/DocumentCenter/View/12919–13024`, dead since the ~2024 CMS migration) and captured
   2022-08. 7 intact Wayback copies are retained in `raw/` as corroborating duplicates;
   8 more were truncated by web.archive.org at exactly 1 MiB (kept as `*.pdf.truncated`;
   the intact Tyler copies are indexed instead).

## Coverage — 125 index rows (116 distinct documents), 8 cycles

| cycle | indexed rows | candidates covered / field | notes |
|---|---|---|---|
| 2011 | 6 | 6/6 ballot | one "financials" per candidate (undated class) |
| 2013 | 14 | 10/10 ballot (primary field) | Castle + T. Gundersen declared→withdrew: declaration/withdrawal only, no financials |
| 2015 | 6 | 6/6 ballot | one "financials" per candidate |
| 2017 | 14 | 7/9 primary field | **Graham + Huh (primary-eliminated) have NO financials in the portal** — publication gap; 6 of the 7 covered exist as two byte-identical catalog copies (both indexed, `duplicate_of` set) |
| 2019 | 26 | 10/12 declared; **6/6 ballot** | see FLAG 2 below; Huh + Phillips: no CF (Phillips' node mis-catalogs North's docs — portal defect) |
| 2021 | 16 | **8/8 ballot (100%)** | 15 filings + 1 catalog duplicate; Walker filed an AMENDED pre-general |
| 2023 | 20 | **7/7 ballot (100%)** + 0/4 withdrawn | survives ONLY in the GRAMA portal |
| 2025 | 23 | **8/8 certified (100%)** | from the live city page; see FLAG 1 |

- **Format split: 9 born-digital `text` / 116 `scanned`** (text: the four 2025-08-05
  pre-primary reports; Lowery-first and Huh-final 2021; Clegg-final, North-final and
  Roberts-10.24 in 2019). Everything else needs OCR/vision — `/cf-vision-transcribe`
  when the extraction phase happens.
- **Election join:** 113/125 rows match a candidate in
  `../election_results/draper_results_by_candidate.csv` (`join_confidence=high`,
  year-scoped full-name token match). The 12 `none` rows are all honest:
  2019 Clegg/DeYoung/Mason/North (declared, withdrew pre-ballot) and
  2025 Green/Lowery (FLAG 1 — the canceled race).

## Per-cycle detail, 2021/2023/2025 (in-scope)

- **2021 (RCV pilot; no primary — all 7 council candidates + unopposed Mayor went to the
  general):** 15 filings = 8 candidates × 7-day pre-general report (received/due
  **2021-10-26**; Farley's is date-verified on the form) + 6 post-general finals (due
  2021-12-02) + Walker's amended pre-general. **Fugal and Farley have no published
  final** — the statutory 30-day-after report was never posted for either (both were
  also-rans); city-publication gap, recorded, not filled.
- **2023 (3 at-large seats; general moved to Nov 21 for the CD2 special):** classes
  present: pre-primary (Bovo 2023-08-07; Rouzer received 2023-08-04 inside her
  compilation), 7-day pre-primary (Johnson 2023-08-29), 28-day pre-general
  (**2023-10-24**, all 6 general candidates), 7-day pre-general (**2023-11-14**, all 6),
  post-general final (**2023-12-21**, 5 of 6 — **Bovo's final was never published**).
  Most candidates' pre-primary reports were not separately catalogued (they may sit
  inside the uncatalogued "22-month-retention" bundles; Rouzer's compilation proves at
  least hers exists). Rouzer (primary-eliminated) has one 16-page phone-photo
  compilation labeled "Campaign Finance Disclosure - Permanent".
- **2025 (Mayor + 4-yr + 2-yr council):** every statutory class published: pre-primary
  2025-08-05 (4 two-year-seat candidates), eliminated-in-primary finals 2025-09-11
  (Herrera Schuster, Sorensen), 28-day 2025-10-07, 7-day 2025-10-28, post-general final
  2025-12-04. **Braxten Rutherford's 12-04 final was NOT filed** — the city page prints
  "did not file report" with no link, and the GRAMA portal has no copy either. Honest
  gap, doubly verified.

## Checked and NOT a source (honest empties)

- **disclosures.utah.gov/Municipal** — a GET-navigable folder tree (contrary to prior
  cities' notes; worth re-checking elsewhere). `salt lake/2021/Draper City/` mirrors
  **8** of the 2021 first-wave PDFs live (a usable fallback URL set;
  `municipal.utah.gov/salt lake\2021\Draper City\…`); **the 2023 Draper folder exists
  but is EMPTY** and there is no 2025 city folder — the state mirror is not a
  substitute for the city sources. Checked 2026-07-13.
- **Salt Lake County Clerk financial-disclosures**
  (`saltlakecounty.gov/clerk/elections/financial-disclosures/`) — hosts county-office,
  metro-township and school-board filings only; cites §10-3-208 but hosts no municipal
  filings; zero Draper content. Checked 2026-07-13.
- **Utah County elections (`vote.utahcounty.gov/financial-disclosures`)** — no Draper
  content (Draper straddles the counties but **Salt Lake County administers the whole
  city election**, and CF filings are made to the *Draper City Recorder* regardless).
  Checked 2026-07-13.
- **2007/2009 cycles** — the GRAMA portal's Elections class returns 0 records for both
  years (searched 2026-07-13): below the portal's digitization floor. Not recoverable
  from any source checked.
- **Wayback for 2023** — comprehensively checked (CDX domain queries for
  campaign/disclos/financ/candidate-name URL patterns; capture lists for the 2023-era
  election pages and per-candidate pages 2098–2107; DocumentCenter id-range 15000–17999):
  the 2023 candidate pages were **never crawled** and no 2023 filing PDF has any
  capture. Without the GRAMA portal the 2023 cycle would be lost.

## Known limits / gaps

- **No dollar extraction yet** — acquisition layer only. Any future totals MUST use the
  cycle-dedup method (`scripts/campaign_finance/cycle_totals.py` pattern), never a blind
  sum — candidates file 2–5 overlapping reports per cycle, and Walker 2021 has an
  amendment that would double-count.
- 2011–2017 filings are single undated "financials" scans per candidate — statutory
  class unknown until extraction (some, e.g. Walker 2013, span the whole cycle in one
  report; Dismuke 2013 is a one-page post-primary Exhibit B summary). Their index
  `date` is that year's **general-election day as a cycle anchor**
  (`date_precision=cycle_anchor`) — NOT a filing date; refine at extraction.
- The 8 `*.pdf.truncated` files in `raw/` are Wayback 1 MiB-truncated partials of 2021
  filings, retained for provenance only — the intact Tyler copies are the indexed ones.
  Do not read the truncated files.
- The 2023 "22-month-retention" bundles (11 catalog attachments, incl. the only records
  for withdrawn candidates Bjelke/Jarman/Portwood/Vawdrey) are in `raw/` but NOT in
  `index.csv` — they are declaration/election-doc packets, not (or not verifiably) CF
  filings; if a bundle later proves to contain a CF report, add it via the normal
  rebuild.
- Redactions are the city's own (addresses/phones/emails blacked out; `_Redacted`
  filenames kept verbatim).

## ⚠ FLAGGED discrepancies / corroborations for the elections dataset (do NOT edit election_results/ from here)

1. **2025 canceled 4-year council race — CF independently corroborates it.** Mike Green
   and Tasha Lowery (the two 4-year-seat candidates certified without appearing on the
   SOVC, Res. #25-49) each **filed three campaign-finance reports** (10-07, 10-28,
   12-04) published on the live city CF page under "City Council At-large (4-year
   seat)". Their filings exist while they appear in no county canvass — exactly the
   pattern of a §20A-1-206 canceled-uncontested race. (Their index rows are the
   `join_confidence=none` 2025 rows.) Jared Turner's withdrawal affidavit
   (2025-09-15, on the candidate-information page + GRAMA portal) is what reduced the
   race to uncontested.
2. **2019: a primary was SCHEDULED and then not held — the CF record proves the
   candidate field collapsed.** The GRAMA portal shows **12 declared 2019 council
   candidates** (vs 6 on the general ballot). Ten filed an early-August "Finance
   Disclosure 1" (due **2019-08-08** per the Recorder’s retained notice letter — the pre-primary
   class for the never-held Aug 13 primary); Clegg filed a **"Final" disclosure 2019-08-29** and North a **"Final"
   2019-09-04** — withdrawal finals. The field evidently shrank to ≤2N=6 and the
   primary was canceled. This is consistent with (and explains) the election dataset's
   "no 2019 primary" finding; the recon's older "2019 election-held status unconfirmed"
   caveat is put fully to rest — general-ballot candidates' Oct/Dec filings + the
   portal's certified `Draper_19G_ESR_111919.pdf` results node confirm it.
3. **2023: four declared candidates never reached the ballot** — Bridget Bjelke, Parry
   Jarman, Dan Portwood (portal Description: WITHDRAWN) and **incumbent Marsha Vawdrey**
   (WITHDREW; she did not seek re-election in the end). They are absent from
   `election_results/` correctly; noted here so a 7-candidate primary field isn't
   mistaken for the full declared field (11).
4. **Portal defect, not an election fact:** the 2019 "Phillips, Joshua" node's
   attachments are James North's documents (mis-catalogued by the city); Phillips' own
   filings, if any, are not in the portal.
