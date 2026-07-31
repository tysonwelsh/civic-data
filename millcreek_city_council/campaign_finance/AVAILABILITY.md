# Campaign finance / financial disclosures — availability & sources

**As-of:** 2026-07-06 · **City:** Millcreek City, Salt Lake County, Utah
**Scope:** municipal candidate campaign-finance disclosure reports — Mayor (at-large) +
City Council (Districts 1–4). Millcreek's entire electoral history is 2016 → present
(it incorporated Dec 2016; there is no pre-2016 record — not a gap).
**Status:** **ACQUISITION ONLY** — raw filing PDFs + `index.csv` retrieved and retained.
The structured contribution/expenditure extraction layer (OCR/vision →
`contributions.csv` / `expenditures.csv` / `cycle_totals.csv`) is a **deferred later
step** (see CLAUDE.md and the double-count-trap note there).

**Result: PARTIAL-but-strong.** **41 campaign-finance filing PDFs** across **four
election cycles (2019, 2021, 2023, 2025)** for **22 distinct candidate-cycles / 18
distinct people**. Filing-level join to `election_results/` = **39/41 (95%)**; the 2
non-joins are the two 2025 **appointment** artifacts (below), not errors. **The 2016
founding cycle and 2017 cycle were NOT located online** (campaign-finance was filed on
paper with the City Recorder before the city began posting PDFs to its DocumentCenter in
2019 — same pre-online-era pattern as South Jordan; see gaps below).

## Where Millcreek campaign-finance filings actually live (verified)

Millcreek candidates file campaign-finance disclosures with the **City Recorder** (Utah
Code 10-3-208) and the city publishes them on **`/547/Disclosures`**
(`https://www.millcreekut.gov/547/Disclosures`) and historically on the Elections page
`/161/Elections`. The city uses a **CivicPlus / CivicEngage** CMS whose document store is
`/DocumentCenter/View/<id>/<slug>`. Two retrieval routes were needed:

1. **Live host — `DocumentCenter/View/<id>/<slug>`.** Serves the **2021, 2023 and 2025**
   filings today (200 / application/pdf). ⚠ The live host **requires a GET with a browser
   UA + Referer and the full `/<slug>` suffix**; a bare `/View/<id>` (and any `HEAD`
   request) returns a 404 HTML stub — fetch through `polite_fetch.py`, not `curl -I`.
   - The **current** `/547/Disclosures` page shows only the **2025 cycle + current elected
     officers** (it is overwritten each cycle — the CivicPlus pattern). 2021/2023 filings
     are no longer *linked* from any live page but their `DocumentCenter` PDFs are **still
     served**; their id→candidate→date mapping was recovered from the Wayback Machine
     (route 3) and then fetched from the live host.
2. **Wayback Machine (first-class tool here).** The **2019 cycle** filings are **404 on the
   live host** and survive only in the Internet Archive. Recovered from the
   **2020-03-04 capture of `millcreek.us/161/Elections`** (the legacy domain — `millcreek.us`
   now 301-redirects to `millcreekut.gov`). CDX → archived HTML (`…/web/<ts>id_/…`) →
   `DocumentCenter/View/<id>/<slug>` links → fetched each archived PDF. `WebFetch` cannot
   reach web.archive.org; all Wayback fetches went through `polite_fetch.py`.
   Saved filenames are prefixed with the filing `YYYYMM`.
3. **`disclosures.utah.gov`** returns a generic state page (no per-city municipal filings);
   the **Salt Lake County** clerk posts county/state filings, not Millcreek municipal — so
   the city site + Wayback are authoritative, consistent with the sibling South Jordan run.

## What was retrieved (by cycle)

| Cycle | Route | Filings | Candidates | Reports/candidate | Format |
|---|---|---|---|---|---|
| **2019** | Wayback (live 404) | 10 | 5 (Mayor: Silvestrini, Vice; D1: Catten; D3: Jackson, Keller) | interim (10/28–29) + summary (11/25–12/5) | **scanned** |
| **2021** | live | 8 | 8 (D2: DeSirant, Clark, Vice, Bagley-Gibson; D4: Uipi, Parker, Boyce, Williams) | 1 combined bundle each | 7 born-digital / 1 scanned (Uipi) |
| **2023** | live | 9 | 3 (D3: Jackson, Springer, Holz) | interim (10/24) + interim (11/14) + summary (12/11–15) | born-digital |
| **2025** | live | 14 | 6 (D2: DeSirant, Gray; D4: Uipi, Gale; + appointed Mayor Jackson, D3 Handy) | interim ×2 + summary (candidates); single (appointees) | born-digital |

**Totals:** 41 PDFs · ~46 MB · 31 born-digital (`format=text`) + 10 scanned
(`format=scanned`, all 2019 + Uipi-2021). RCV cycles (2021, 2023) are flagged in the
election data, not here — the CF reports themselves are cycle filings regardless of tally
method.

## Election-record mismatches — honest artifacts (flagged, NOT forced)

Campaign-finance data surfaces genuine election-record asymmetries. **Nothing here was
edited into `election_results/`** — these are recorded as-is:

1. **2025 appointed Mayor Cheri Jackson** and **2025 appointed D3 Nicole Handy** each have
   a single CF filing but **no 2025 election contest** — both were **appointed** in Nov 2025
   (Jackson to Mayor to finish Silvestrini's term; Handy to the D3 seat Jackson vacated).
   These are the two filing rows with `in_election_results=no`. **A filer without a held
   race is a real, honest artifact** of the appointment, exactly as `election_results/`
   documents (no 2025 mayoral race row exists). Handy has **no** row anywhere in
   `election_results` (never elected).
2. **2023 Mayor (Silvestrini) and D1 (Catten)** — **cancelled-uncontested** races (UCA
   20A-1-206). **No campaign, hence no CF filing** for either — and indeed none was found.
   The **inverse** artifact: a seat "winner" with no filing because there was no campaign.
   Consistent, not a gap. (2023's only contested seat, D3, has full filings.)
3. All other filers (20 candidate-cycles) **join person+year to
   `election_results/millcreek_results_by_candidate.csv` exactly**, including every
   eliminated RCV candidate (2021 Bagley-Gibson, Vice, Boyce, Williams; 2023 Holz).

## Honest gaps (checked; recorded, not filled) — see `unrecovered.csv`

- **2016 founding cycle + 2017 cycle — NO campaign-finance filings online.** The city's
  DocumentCenter CF numbering **starts at 2019** (lowest CF ids ≈ 1215). The 2018-era
  legacy WordPress `/elections/` page (Wayback 2018-09) linked only a budget-"Financials"
  page and the state disclosure site — **no candidate CF PDFs**. Pre-2019 filings were kept
  on paper by the Recorder and were never published online (same pre-online-era pattern as
  South Jordan's pre-2019 gap). ~10 candidate-cycles (2016 founding Mayor + 4 districts, in
  primary + general; 2017 D2 + D4) are affected. **Not fabricated; recorded as a gap.**
- **Conflict-of-Interest / candidate financial-disclosure statements are OUT OF SCOPE.**
  The `/547/Disclosures` page also carries a **separate disclosure regime** — Utah
  elected-officer **annual Conflict-of-Interest** statements (filed Jan 2026: Jackson 5994,
  Catten 5983, DeSirant 4971+6034, Handy 5995, Uipi 6096) and 2025 candidate
  financial/COI statements at candidacy (Gale 5707, DeSirant 5708, Gray 5711, Uipi 5736).
  These are **not campaign-finance (contribution/expenditure) reports** and were
  deliberately **not harvested**; their ids are logged here for a future pass.
- **`_Redacted` filings (2025 Gray & Gale, 2023 Holz).** The city posts city-redacted
  copies (donor PII removed); these are the only public versions. Retained as-is; noted
  per row (`redacted=yes`).

## Provenance

Every byte fetched through `scripts/polite_fetch.py` (browser UA, ≥1s/host, ret/backoff),
which wrote `raw/live/_fetch_log.jsonl` and `raw/wayback/_fetch_log.jsonl` (url, final_url,
status, bytes, sha256, content_type, retrieved_utc). `index.csv` carries `sha256` + `bytes`
+ `doc_id` + `final_url` per file. `retrieved_date` = 2026-07-06 (frozen clock).
