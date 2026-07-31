# White City — Campaign-Finance Disclosures: Availability

**As-of:** 2026-07-13 · **Layer:** ACQUISITION-ONLY (raw filings retained; no OCR/vision
extraction, no dollar totals computed — those are deferred). **Cycles in scope:** 2023
(Metro Township Council At-Large) + 2025 (first city-era election: Mayor + Council At-Large
B + At-Large C).

White City (~5,000 pop., Salt Lake County) is a **metro township → city** (HB35, effective
2024-05-01). Its elections are **administered by the Salt Lake County Clerk**, but municipal
campaign-finance filings are **NOT** hosted by the county or the state; the record is what the
**city itself publishes on its Streamline site** (`whitecity.utah.gov`). **28 filings** were
recovered — all from the **2025 city-era cycle**: **18 campaign-finance money reports** (Utah
Code 10-3-208) + **10 conflict-of-interest disclosures** (Utah Code 10-3-1301, captured per the
SKILL COI note as `filing_type=coi_disclosure`). **The 2023 (and all earlier metro-township)
cycles have NO campaign-finance filings published anywhere online** — an honest gap (see below).

## What was checked (search order)

1. **State `disclosures.utah.gov/Municipal` GET-navigable folder tree** (`salt lake_<year>_…`).
   Enumerated the per-county → per-year → per-entity structure directly. **White City has NO
   subfolder in ANY year (2009–2025).** The metro-township-origin entities as a class — **White
   City, Kearns, Magna, Copperton, Emigration Canyon** — are **entirely absent** from the state
   municipal tree (verified across 2017/2019/2021/2023). The state's **2025** entry is a
   link-farm that points White City to its **own** page `whitecity.utah.gov/disclosure-statements`
   — the state hosts no White City PDFs. (Directory *listing* on `municipal.utah.gov` is 403;
   individual files resolve — but there are none for White City.)
2. **Salt Lake County Clerk financial-disclosures page**
   (`saltlakecounty.gov/clerk/elections/disclosures/`). Hosts **county-office COI disclosures
   only** (2025/2026 county races). **No White City municipal candidates** (Perry/Flint/Price/
   Denning/Mahoney/Cardenaz/Shelton/Huish) and **no campaign-finance (contribution/expenditure)
   filings** appear. The county does not host White City's municipal filings.
3. **The Streamline city site — PRIMARY and the only source that yields filings.**
   - **`whitecity.utah.gov/elections`** — the **2025 campaign-finance money reports** (18 PDFs:
     6 candidates × 3 reports each; see the table). This is where the real contribution/
     expenditure data lives.
   - **`whitecity.utah.gov/conflict-of-interest-disclosures`** (the page titled "Disclosure
     Statements") — **10 conflict-of-interest ethics forms** (2025 candidate COIs + 2025/2026
     annual elected-officer COIs). A *different* statutory instrument from campaign finance.
   - Streamline serves labeled `<a href="/files/<hash>/…pdf">` anchors (browser UA); hashes are
     opaque — the anchors were harvested, never guessed.
4. **Wayback Machine** (`web.archive.org` CDX, via `polite_fetch.py`). Recovered the legacy
   `whitecity.specialdistrict.org` capture set. The archived **2023 election pages**
   (`/2023-municipal-election-candidates-and-information`,
   `/2023-white-city-metro-township-election-declaration-of-candidacy-june-1-7`) carry only a
   candidate-info **notice** PDF — **no 2023 campaign-finance reports**. No finance PDFs exist in
   any legacy capture. Wayback confirms the 2023 gap is real, not a CMS-migration loss.

## Coverage vs the election roster (`election_results/white_city_races.csv`)

| Cycle | Ballot candidates (office) | Finance money reports held | Status |
|---|---|---|---|
| **2019** (metro twp) | Little, **Perry**, **Flint**, Cutler (Council At-Large) | **none** | GAP — no filings published |
| **2023** (metro twp) | **Flint**, **Shelton**, **Huish**, Van Horn, West (Council At-Large) | **none** | **GAP — no filings published anywhere** |
| **2025** (city) | **Perry** vs Flint (Mayor); **Price** vs Denning (At-Large B); **Mahoney** vs Cardenaz (At-Large C) | **3 each for all 6 candidates = 18** | **COMPLETE per the ballot roster** |

Every 2025 ballot candidate (both winners and losers) filed the full three-report series
(Oct 7, Oct 28, Dec 4). **2025 coverage is complete.** In addition, 10 COI ethics forms cover
the 2025 candidates and the seated 2025/2026 officials (Perry, Price, Shelton, Huish).

## Threshold-exemption / dollar reality

- **2025 — SUBSTANTIVE, NOT threshold-exempt.** Contrary to the small-entity "likely exempt"
  expectation, all six 2025 candidates filed real money reports with itemized activity:
  - **Phillip Cardenaz** (At-Large C, incumbent, lost): **$1,050 contributions** — Greg Shelton
    $400, Misty Stoakes $300, Ashtree Legal Services $250, + $100 small-dollar; expenditures
    incl. Victory Signs $389.48, Hobby Lobby $121.40. (Note: a councilmember, Greg Shelton,
    donated to Cardenaz.)
  - **Paulina Flint** (Mayor, lost): an **$820 self-loan** + $500 (Yianni Ioannou) + $80 (Lina
    Barkey). Her Oct-7 and Dec-4 reports restate identical entries (cumulative filer).
  - **Douglas Denning** (At-Large B write-in, lost): ~**$978 self-funded** printing/flyer
    expenditures (printing $903.73, paper $30, ink $45).
  - **Allan Perry** (Mayor, won), **Linda Price** (At-Large B, won), **Neil Mahoney** (At-Large
    C, won) each filed all three reports (several are scanned; dollar extraction deferred).
- Exact per-candidate/per-cycle totals are **not computed in this acquisition layer.** See the
  double-count note below before producing any dollar figure.

## Double-count / dedup (SKILL §6)

The Utah 10-3-208 reports here are **cumulative period statements** (each "Prior to General
Election" and the "Final Report" restates cycle-to-date figures — **confirmed cumulative for
Flint**, whose Oct-7 entries reappear verbatim on her Dec-4 Final). Therefore
**`is_incremental=no` on every money report, and the Dec-4 Final is the authoritative
per-candidate total — do NOT sum the three reports.** One documented caveat: **Cardenaz's Final
(Dec 4) is under-filled** ($0 totals; his actual activity is itemized on his Oct-7 report), so
his per-cycle total must be taken from the Oct-7 report, not the Final. Any dollar total MUST go
through the repo dedup (`scripts/campaign_finance/cycle_totals.py`), never a row sum — the mixed
filing behaviour (a cumulative Flint vs an under-filled Cardenaz Final) is exactly the trap the
SKILL warns about.

## Discrepancy FLAGS (recorded here only — do NOT edit `election_results/`)

1. **2023 metro-township campaign finance is entirely unpublished — an honest gap that ALIGNS
   with the known 2017/2019/2021 election-record gap.** `recon.md` and `election_results/CLAUDE.md`
   flag that the metro-township cycles (2017/2019/2021) were the fragile ones for the SLCo SOVC.
   The finance record independently confirms the metro-township era was poorly digitized: **no
   White City finance filing exists for any pre-2024 cycle** — not on the state tree, the county,
   the city site, or Wayback. This is consistent with (a) metro-township candidates being
   threshold-exempt / filing on paper with the MSD-staffed township recorder and nothing being
   posted, and (b) the general thinness of the metro-township digital record. **No new election
   contest is surfaced or contradicted** — the 2023 winners (Flint/Shelton/Huish) are already in
   `white_city_races.csv`; this dataset adds no 2023 money data to reconcile.
2. **A councilmember donated to a candidate.** Cardenaz's Oct-7 report itemizes a **$400
   contribution from Greg Shelton** (a sitting White City councilmember, Seat A). Recorded here
   as source fact; no action on other layers.
3. **Water-district decoy correctly excluded.** The state 2025 link-farm lists
   `wcwid.utah.gov/disclosures` — the **White City Water Improvement District** (a *separate*
   special district). Its disclosures were **NOT** ingested (per the recon decoy warning). The
   only White City *governing-body* finance is on `whitecity.utah.gov`.
4. **COI vs campaign finance.** The city's page titled "Disclosure Statements" holds
   **conflict-of-interest ethics forms** (Utah Code 10-3-1301 / 67-16-1), a different statutory
   instrument from campaign finance. They are captured as `filing_type=coi_disclosure` (per the
   SKILL COI note), NOT mixed into the money-report totals. Two are 2025 candidate COIs anchored
   to the June candidacy window; the rest are 2025/2026 annual elected-officer COIs (Shelton
   1/29/2026 and Huish 1/28/2026 carry printed form dates; the others are Jan-window anchored).
   Filename note: `2025 Conflict of Interest (1).pdf` is in fact **Linda Price's 2026** annual
   officer COI (content dated 2026; she was seated Jan 2026) — retained as `2026_price_coi.pdf`.

## Formats

- **Born-digital text (`format=text`, 13 files):** Flint's 3 reports, Denning Oct-28 + Final,
  Perry Oct-28, Cardenaz Oct-7 + Final, and 6 COIs (Shelton 2025, Price 2026, Perry 2026,
  Shelton 2026, Huish 2026). Parse cleanly with `pdftotext -layout`.
- **Scanned (`format=scanned`, 15 files):** all of Price's + Mahoney's money reports, Perry
  Oct-7 + Final, Denning Oct-7, Cardenaz Oct-28, and the 4 scanned COIs (Perry candidate,
  Denning, Cardenaz 2025, Price 2025, Huish 2025). Image scans — dollar/vision extraction deferred.
- **Extraction deferred:** `extraction_method = "none (raw acquisition; OCR/vision deferred)"` on
  every row. No `text/` sidecars and no dollar parsing in this layer.

## Honest gaps / non-issues

- **No pre-2024 (metro-township) campaign finance** is published — see FLAG 1. The earliest
  in-scope cycle that yields anything is **2025** (the first city-era election).
- **2019/2021/2017:** no finance filings (metro township — same gap). Consistent with the
  election-record note in `election_results/CLAUDE.md`.
- **Conflict-of-interest forms** are a separate ethics regime; they are captured here (per the
  SKILL COI instruction) but must not be summed with campaign-finance dollars.
- **White City Water Improvement District** filings (`wcwid.utah.gov`) are a decoy and were
  deliberately excluded.

## 2026-07-17 — STRUCTURED MONEY LAYER BUILT (supersedes "extraction deferred")

The acquisition-only posture above is superseded for the **money reports**: `build_finance.py`
(family `vision_cache`) now extracts dollar totals into `contributions.csv` (48) /
`expenditures.csv` (48) / `filing_totals.csv` (18) / `cycle_totals.csv` (6). `validate_finance.py`
PASS. The 10 COIs remain out of scope (not extracted). See `CLAUDE.md` for full build notes.

- **All 18 money reports are now transcribed** (`vision/` = 18 caches). The 10 fully-scanned
  reports were pre-staged 2026-07-13; the remaining 8 (`format=="text"`) were transcribed at
  structuring time — 7 born-digital via `pdftotext` and 1 (Perry Oct-28, image schedules) via
  Read-tool page images. The "extraction deferred / dollar extraction deferred" language in the
  **Formats** and **Threshold-exemption** sections above is therefore historical.
- **Per-candidate cycle totals** (`cycle_totals.csv`, the authoritative per-race figure — never
  sum `filing_totals`): Perry $7,730.50 raised / $7,706.47 spent (Mayor, won); Flint $3,550 /
  $2,627.08 (Mayor, lost); Price $695.82 / $695.82 (At-Large B, won); Denning $978.73 / $978.73
  (At-Large B write-in, lost); Mahoney $1,543.03 / $1,543.03 (At-Large C, won); Cardenaz $1,050 /
  $1,763.51 (At-Large C, lost). Perry + Cardenaz carry documented `cycle_overrides.csv` reasons.
- **The dollar-reality bullets above are confirmed by the extraction:** the $400 Shelton→Cardenaz
  gift (Cardenaz Oct-7), Flint's $820 self-loan + $500 Loannou + $80 Barkey (Flint reports), and
  Denning's ~$978 self-funded printing (Denning Dec-4 Final) are all in the itemized rows. The
  **`is_incremental=no on ALL money reports`** guidance in the index/schema note is refined:
  regimes are per-candidate (Flint/Denning cumulative; Perry/Price/Mahoney/Cardenaz per-period) —
  the derived `cycle_totals.csv` encodes the correct dedup.
- **Honest UNKNOWNs (by design, not gaps):** Mahoney Final, Cardenaz Oct-28, Price Final print
  non-zero covers over BLANK itemization schedules → totals-only, reconciliation left blank.
