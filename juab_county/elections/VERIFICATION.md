# Juab County elections — verification & reconciliation

**Verification date:** 2026-07-20. Method: the canonical layer is built from the
**Channel C** Enhanced Voting state API (precinct-level) and reconciled against the
**Channel A** Juab County Clerk canvass PDFs and **Channel B** Lt. Governor per-county
canvass certifications. Every number traces to a file in `raw/` (see `sources.csv`,
79 byte-verified rows). Names are recorded verbatim.

## 1. Internal reconciliation — precinct detail vs certified total

The long file stores, per contest × candidate, an authoritative **`Certified Total`**
row (the EV portal's certified contest total, == the canvass PDF) plus the
**`Precinct`** breakdown. EV **privacy-suppresses** low-count split precincts
(`voteCount=null` → `votes='' , suppressed='True'`), so the certified total is ≥ the
sum of attributed precincts.

- **133 candidate rows reconcile EXACTLY** (attributed precinct sum == certified total).
- **60 candidate rows** have a small positive gap **fully explained by suppressed
  precincts** (e.g. 2024 General *County Commission Seat C*: certified 5,433 vs
  attributed 5,429 = the 2 suppressed splits `Eureka #6` + `Nephi #5:U2`).
- **0 overcounts** — an attributed sum never exceeds the certified total (no
  double-counting). All 2023/2025 **municipal** contests carry zero suppression and
  reconcile exactly; suppression touches only a handful of 2024/2026 county/state/
  school contests where a low-population split precinct is hidden.

`build_elections.py` sums only the `Certified Total` rows, so the derived
`election_results_by_contest.csv` matches the certified canvass regardless of
suppression, and flags `suppressed='true'` where any precinct was hidden.

## 2. Cross-source reconciliation — EV vs the canvass PDFs

Programmatic candidate-total comparison, EV certified totals vs the born-digital
single-column summary PDFs (0 mismatches):

| PDF (channel) | election | candidate totals matched |
|---|---|---|
| Clerk `2023-11-general-official.pdf` (A) | 2023 municipal general | **29 / 29 exact** |
| Lt-Gov `P25_Canvass_Juab.pdf` (B) | 2025 municipal primary | **18 / 18 exact** |

Spot examples (EV == PDF): **Nephi Council 2023** Worwood 895 / Cowan 812 / Parady 764
/ Ostler 693 / Bradley 621 / Miller 572; **Nephi Mayor 2025** Seely 1,298;
**County Commission Seat C 2024** Kenison 5,433; **County Recorder/Surveyor 2024
primary** Zirbes 1,349; **Juab County School Board Dist 1 2024** Blackett 813 /
Beutler 627. The multi-column even-year Lt-Gov certifications (G24/P24) print a TOTAL
column ahead of per-precinct columns; their totals were confirmed manually (above) —
a naive line scraper reads the first precinct column, not a data mismatch.

## 3. Cross-check vs the audited Nephi city layer

`election_results_by_contest.csv` (jurisdiction_slug='nephi') reproduces the seated
Nephi council exactly as `../../nephi_city_council/election_results/nephi_races.csv`:
2023 general → Worwood, Cowan, Parady; 2025 general (2 seats) → Douglas, Callaway;
2025 Mayor → Seely (unopposed). The repo had already proven Nephi reconciles to the
county source; this county canvass is that source, extended to all Juab jurisdictions.

## 4. Ceilings & honest gaps

- **Precinct ceiling:** EV publishes precinct **totals only** — no per-vote-method
  split (Election Day / By Mail / Early). `vote_method` is `Total`/`Precinct`, never a
  method. The Clerk/Lt-Gov SOVC-style PDFs *do* carry method columns but are not
  machine-ingested here (owner-gated cheap tier); they are retained raw for audit.
- **Precinct label variance across vintages (verbatim, NOT normalized):** 2025 EV
  prefixes the CountyID (`12Nephi #3`) while 2023/2024 do not (`Nephi #3`); overseas/
  federal-only ballots appear as pseudo-precincts (`Federal`, `Federal District 2/4`)
  and split precincts as `:U`/`:U1`/`:USQ`. Kept verbatim; reconciliation is per-contest
  so it is unaffected. Do not treat the prefixed/unprefixed forms as different places.
- **2023 Sept-5 municipal primary — Clerk PDF only.** The EV portal carries an empty
  `primary09052023_Demo` slug (all voteTotal=0); the real canvass is
  `raw/clerk/2023-09-05-primary-official.pdf`, hand-keyed contest-grain (no precinct).
  Named-candidate sums are below the printed *Contest Totals* by the write-in/
  unallocated remainder (Nephi 4,214 named vs 4,608 printed) — recorded as-is, never
  back-filled.
- **CONFIRMED HONEST GAP — 2019 & 2021 municipal cycles have NO official canvass
  anywhere.** The Juab Clerk results page, the EV portal, and vote.utah.gov all floor at
  **2023/2024**. The canonical county layer therefore **starts 2023**. (Nephi's city-side
  2019/2021 rows keep their existing news-archive *unofficial* caveat — that is the city
  module's scope, not this one.) No unofficial numbers are ingested into the county
  canonical.
- **2024 Presidential Preference Primary** (`primary03052024`) and the **CD-2 recount**
  (`PrimaryCD2Recount2024`) are out of governance scope — not harvested.
