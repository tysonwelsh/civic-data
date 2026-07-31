# campaign_finance/ — availability & gap log

As-of **2026-07-13**. Additive acquisition-only dataset; no existing dataset modified.

## What exists

- **City website (CivicPlus)** is the authoritative and effectively ONLY source. Murray
  self-hosts all municipal campaign-finance statements:
  - **Current page:** `https://www.murray.utah.gov/1903/Campaign-Finance-Statements`
    (created Nov 2021) — carries the **2019, 2021, 2023, 2025** cycles.
  - **Retired page:** `/1460/Campaign-Finance-Statements` (live-404 since ~2024) — held
    the **2017** cycle. Recovered via the Wayback Machine (captures 2017-08 → 2021-04);
    the 16 linked DocumentCenter PDFs are **still served live** by the city
    (`DocumentCenter/View/<docid>` 301s to the named file), so all 2017 bytes came from
    the city, not the archive.
- **State (`disclosures.utah.gov/Municipal/`)**: checked 2026-07-13 — the
  `salt lake_2021_Murray City` and `salt lake_2023_Murray` folders are **empty link
  stubs**, and the 2025 entry just links back to the city's /1903 page. Not a source.
- **Salt Lake County clerk** (`saltlakecounty.gov/clerk/elections/financial-disclosures/`):
  checked 2026-07-13 — cites Utah Code §10-3-208 but hosts **no Murray municipal
  filings**. Not a source.

## Coverage

- **131 filings across 5 cycles**: 2017 (16), 2019 (21), 2021 (21), 2023 (34), 2025 (39).
- **39 born-digital `text` / 92 `scanned`** (incl. one native `.xlsx` [text] and one
  image-based `.docx` [scanned] — the city posts whatever candidates email in).
- **Every candidate with posted filings is covered.** In-scope-cycle election join:
  **87 rows `yes` (high)** to `../election_results/murray_results_by_candidate.csv`;
  7 rows `no` (all explained below); 37 rows `below_floor` (2017/2019 cycles, which the
  election dataset deliberately omits — data floor 2020).

## DISCREPANCY FLAGS for the elections layer (do NOT edit election_results — review items)

1. **The filings prove a 2021 municipal primary that `murray_races.csv` does not carry.**
   The dataset (and its CLAUDE.md) says "No 2021 primaries — every 2021 Murray race drew
   ≤2 candidates." But the city's CF page lists **four 2021 mayoral candidates** (Bullen,
   Fitzgerald, Hales, Teemsma) with Aug 3 *pre-primary* statements and Sept 8/9
   *post-primary (eliminated)* finals for Fitzgerald and Teemsma, and **three D4
   candidates** (Rasmussen, Galt, Turner) — i.e. a 2021 primary (Mayor + D4) was held.
   The 2021 primary SOVC likely sits unparsed in the county archive alongside the
   recovered 2021 general workbook.
2. **Skylar L. Galt (2021 D4)** appears on the CF page as a candidate but with **zero
   posted filings**, and is absent from `election_results` (no 2021 primary rows). Both
   a city-publishing gap (no filings) and part of flag #1.

Neither flag was applied to `election_results/` — acquisition layer only.

## Known limits / honest gaps

- **Vision transcription DONE for all in-scope scanned filings (2026-07-17);
  structured dollar layer still deferred.** The `/cf-vision-transcribe` Read-tool pass
  cached **63 `vision/*.json`** files — every scanned filing for the 2021/2023/2025 cycles
  (the 2025 Evans image-based `.docx` included; the Jim Brass 2023 withdrawal *affidavit*
  correctly excluded — not a finance statement). These caches carry the itemized
  contributions/expenditures + verbatim printed cover totals, but **no `build_finance.py`
  consumes them yet** (structured contributions/expenditures/cycle-totals CSVs remain
  owner-gated). The **2017 + 2019 below-floor scanned cycles are NOT transcribed** (honest
  future candidates). **Do not sum anything from these caches without the cycle-dedup rules**
  (multiple filings per candidate per cycle; amended filings restate their originals; printed
  cover totals were retained verbatim and NOT reconciled against candidate arithmetic).
- **Candidates with no filings posted:** Joe Christensen (2025 Mayor, withdrew — the
  page marks him "(Withdrew)" with no documents) and Skylar L. Galt (2021 D4, above).
  Honest empties — the city posted nothing.
- **Missing report-slots within candidates are mostly source-explained:** the city page
  itself prints "Disclosure not required" for slots where a candidate had no primary
  (e.g. 2021 D2, 2023 D5 pre-primary slots) or was eliminated (no later reports due).
  Not gaps.
- **Aaron Lee Holbrook (2025 D2)**: the document posted under his "August 5, 2025
  Disclosure" label (docid 17146, native xlsx) has a server filename of `09_2025` and a
  Schedule B identical to his Sept 11 signed PDF (17144) — the two appear to be native +
  signed versions of **one September statement**; a distinct Aug 5 pre-primary statement
  may not actually be posted. Flagged in the index `note`; resolve at transcription time.
- **Rosalba Dominguez 2019**: the city **replaced her original 2019 filings (docids
  10077/10079/10403/10514/10513) with redacted re-uploads on 2023-03-09** (docids
  13758–13763, server filenames `*_Redacted`). The redacted set is what we retain — the
  originals were withdrawn deliberately (privacy) and were not chased. Two of the
  re-uploads are mislabeled on the page (13760 is a duplicate stamped copy of the
  Primary statement, not an Oct 29 amendment; 13758 is the amended *General*, listed
  under Dec 5) — evidence and flags in the index `note` column. One stale original link
  (10513) still appeared on the page as late as the 2024-06 Wayback capture and has
  since been removed by the city.
- **2015 and earlier**: no city CF page existed (the /1460 page begins with 2017; no
  earlier campaign-finance URL surfaced in Wayback for murray.utah.gov). Utah municipal
  filings that old are typically paper records at the city recorder — GRAMA territory,
  out of scope.
- **Jim Brass 2023 (docid 14399)** is a *Candidacy Withdrawal Affidavit*, not a finance
  statement — indexed with blank `filing_type` for completeness (it explains why his
  only finance filing is a Final).
- **Related but out of scope:** `/2123/Disclosure-Statements` hosts Utah Code
  **conflict-of-interest** disclosure statements (sitting officials 2024/2026 + the 2025
  candidate slate). Different instrument; not campaign finance; not indexed here.

## How verified / method

- All bytes fetched GET-only via `scripts/polite_fetch.py` (browser UA, throttled,
  retried); url/status/bytes/sha256 logged per attempt in `raw/_fetch_log.jsonl`.
- Filenames are `YYYYMM_<Candidate>_<docid>.<ext>` (upload-period prefix — basenames
  collide across filing periods otherwise).
- Candidate/report-class mapping parsed from the /1903 page structure and cross-checked
  against the **server-side descriptive filenames** every DocumentCenter redirect
  exposes (`final_url` in the fetch log) — mismatches became the flags above.
- 2019 district assignments (absent from the current page) recovered from the archived
  /1460 page (Wayback 20191208): D1 Martinez/Pehrson/Nicponski; D3 Brass/Dominguez/
  A. Thompson; D5 B. Hales.
- 2017 upload dates recovered from the Wayback 20211215 capture of /1903 (which then
  still listed the 2017 cycle with dates).

## 2026-07-18 — STRUCTURED DOLLAR LAYER BUILT (contributions / expenditures / cycle totals)

The deferred structured pass is DONE. `build_finance.py` + `murray_text.py` (family
`vision_cache`) now emit `contributions.csv` (1,446 rows) / `expenditures.csv` (1,046) /
`filing_totals.csv` (130) / `cycle_totals.csv` (46 candidate-cycles), all regenerable.
`validate_finance.py` PASS (0 FAIL; the 1 WARN is the deliberately-excluded Jim Brass
affidavit). See `CLAUDE.md` for the full build record.

- **Money coverage:** 93 filings transcribed (63 `vision/` scanned caches + **30 `text_cache/`
  born-digital** caches); 74 both-sides reconcile. Murray's born-digital `format=text` filings
  carry REAL money (Ben Peck 2025 = $5,700 / $4,002.81) and ARE parsed — not the midvale
  "text-is-junk" case. The **2017 (16) + 2019 (21) below-floor** filings remain inventory-only
  (empty totals, dated reason) — acquired, not transcribed.
- **CYCLE TOTALS — per-period form.** Murray filings are per-period (each Covers a disjoint
  range), so a candidate's final/summary report is itself a period report. 23 documented
  `cycle_overrides.csv` rows set the correct per-candidate cycle = sum of all period covers
  (cycle_totals' generic summary-vs-interims rule undercounted by dropping the final period).
  Read `cycle_totals.csv` for any race total — never sum `filing_totals`.
- **Elections-layer discrepancy flags (#1/#2 above) are UNCHANGED and now MONEY-BACKED:** the
  2021 Mayor + D4 primary the CF filings imply (Fitzgerald/Teemsma post-primary "eliminated"
  finals; Bullen amended pre-general) is now visible as structured dollars; still NOT edited
  into `election_results/` (acquisition/structuring layer only — elections-review item stands).
- **Rosalba Dominguez 2023 (docid 14463)** confirmed a genuine 2023 D3 filing (form header +
  Apr–Aug 2023 transaction dates), despite a stray "2019 re-upload" note in its scanned cache
  `_meta` — the ~$9.7k belongs to 2023, not 2019.
